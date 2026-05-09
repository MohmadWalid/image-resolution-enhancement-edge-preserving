import numpy as np
import cv2
from scipy.ndimage import zoom
import math


# =========================================================
# Cuckoo Search (CS) Optimization for gain factor k
# Sections 4.2 & 4.3 of the paper
# =========================================================

def levy_flight(beta=1.5):
    """
    Generates a step length using Mantegna's algorithm for Levy flight.
    Section 4.3, Eq. after (5).
    """
    # Use math.gamma instead of np.math.gamma
    numerator = math.gamma(1 + beta) * np.sin(np.pi * beta / 2)
    denominator = math.gamma((1 + beta) / 2) * beta * (2 ** ((beta - 1) / 2))
    
    sigma_u = (numerator / denominator) ** (1 / beta)
    sigma_v = 1.0

    u = np.random.normal(0, sigma_u)
    v = np.random.normal(0, sigma_v)
    step = u / (abs(v) ** (1 / beta))
    return step


def cuckoo_search(fitness_fn, n_nests=10, n_generations=20,
                  k_min=0.5, k_max=3.0, pa=0.25, beta=1.5):
    """
    Cuckoo Search to optimise the USM gain factor k.
    Eq. (5) and Algorithm 2 of the paper.

    Args:
        fitness_fn : callable(k) -> scalar; higher = better (we use PSNR proxy).
        n_nests    : number of host nests (population size).
        n_generations: number of generations g.
        k_min/max  : search bounds for k.
        pa         : probability of host discovering alien egg.
        beta       : Levy exponent (1 < beta < 3).

    Returns:
        best_k (float): optimised gain factor.
    """
    # Initialise nests at random positions in [k_min, k_max]
    nests = np.random.uniform(k_min, k_max, n_nests)
    fitness = np.array([fitness_fn(k) for k in nests])
    best_idx = np.argmax(fitness)
    best_k = nests[best_idx]
    best_fitness = fitness[best_idx]

    for _ in range(n_generations):
        # --- Levy flight: pick a random cuckoo and generate new solution ---
        i = np.random.randint(n_nests)
        step_size = 0.01 * levy_flight(beta) * (nests[i] - best_k)
        new_k = np.clip(nests[i] + step_size, k_min, k_max)
        new_fitness = fitness_fn(new_k)

        # Replace a randomly chosen worse nest
        j = np.random.randint(n_nests)
        if new_fitness > fitness[j]:
            nests[j] = new_k
            fitness[j] = new_fitness

        # --- Abandon a fraction pa of worst nests & build new ones ---
        n_abandon = max(1, int(pa * n_nests))
        worst_idx = np.argsort(fitness)[:n_abandon]
        nests[worst_idx] = np.random.uniform(k_min, k_max, n_abandon)
        fitness[worst_idx] = np.array([fitness_fn(k) for k in nests[worst_idx]])

        # Track best
        cur_best = np.argmax(fitness)
        if fitness[cur_best] > best_fitness:
            best_k = nests[cur_best]
            best_fitness = fitness[cur_best]

    return best_k


# =========================================================
# LA Filtering  (Algorithm 1)
# =========================================================

def calculate_local_variance(image):
    """
    3×3 local variance of the image.
    Equations (1) and (2) from Algorithm 1.
    """
    image = image.astype(np.float64)
    mean_img = cv2.blur(image, (3, 3))
    mean_sq_img = cv2.blur(image ** 2, (3, 3))
    var_img = mean_sq_img - mean_img ** 2
    return np.maximum(var_img, 0)


def get_gaussian_kernel(cp):
    """
    LA Gaussian kernel whose centre weight equals cp.
    Algorithm 1.
    """
    kernel = np.array([
        [1, 2, 1],
        [1, cp, 1],
        [1, 2, 1]
    ], dtype=np.float64)
    return kernel / (cp + 12)


def local_adaptive_filter(lr_float):
    """
    Applies the Local Adaptive (LA) filter.
    Algorithm 1: varies centre-pixel weight Cp based on local variance.
    """
    var_img = calculate_local_variance(lr_float)
    v_max = np.max(var_img)
    v_min = np.min(var_img)
    S = (v_max - v_min) / 6.0

    # High variance → small Cp (more blur to highlight HF by subtraction)
    # Low variance  → large Cp (less blur to preserve smooth regions)
    cp_values  = [2,  3,  4,  8,  16, 32]
    conditions = [
        var_img >  (v_max - S),
        (var_img > (v_max - 2 * S)) & (var_img <= (v_max - S)),
        (var_img > (v_max - 3 * S)) & (var_img <= (v_max - 2 * S)),
        (var_img > (v_max - 4 * S)) & (var_img <= (v_max - 3 * S)),
        (var_img > (v_max - 5 * S)) & (var_img <= (v_max - 4 * S)),
        var_img <= (v_max - 5 * S),
    ]

    h_ab = np.zeros_like(lr_float)
    for cp, cond in zip(cp_values, conditions):
        if not np.any(cond):
            continue
        kernel   = get_gaussian_kernel(cp)
        filtered = cv2.filter2D(lr_float, -1, kernel)
        h_ab[cond] = filtered[cond]

    return h_ab


# =========================================================
# e-spline: Edge detection + expansion  (Section 4.5)
# =========================================================

def edge_expansion(g_hr):
    """
    Detects edges on the B-spline HR image and returns the ADDITIVE
    edge-correction layer G_e (not the modified image itself).

    Fixes the paper's Equation (15):
        G_RHR = G_HR + G_e

    The original code overwrote G_HR in-place, which skipped the
    explicit additive fusion required by Eq. (15).

    Equations (9)–(14) are followed exactly.
    """
    hr_uint8 = np.clip(g_hr, 0, 255).astype(np.uint8)
    edges    = cv2.Canny(hr_uint8, 100, 200)

    # SDh and SDv kernels — Eqs. (9) and (10)
    kernel_h = np.array([
        [ 1/4, 0, -1/4],
        [ 1/2, 0, -1/2],
        [ 1/4, 0, -1/4]
    ], dtype=np.float64)

    kernel_v = np.array([
        [ 1/4,  1/2,  1/4],
        [   0,    0,    0],
        [-1/4, -1/2, -1/4]
    ], dtype=np.float64)

    sd_h = cv2.filter2D(g_hr, -1, kernel_h)
    sd_v = cv2.filter2D(g_hr, -1, kernel_v)

    # G_e accumulates the corrections that will be added to G_HR (Eq. 15)
    g_e = np.zeros_like(g_hr)

    # Working copy so we read original values while writing corrections
    expanded = g_hr.copy()
    h, w = g_hr.shape
    edge_y, edge_x = np.where(edges > 0)

    for y, x in zip(edge_y, edge_x):
        if y < 2 or y >= h - 2 or x < 2 or x >= w - 2:
            continue

        if abs(sd_h[y, x]) >= abs(sd_v[y, x]):
            # Vertical-direction edge — Eqs. (11) & (12)
            new_left  = 0.5 * (g_hr[y, x - 1] + g_hr[y, x - 2])
            new_right = 0.5 * (g_hr[y, x + 1] + g_hr[y, x + 2])
            g_e[y, x - 1] += new_left  - g_hr[y, x - 1]
            g_e[y, x + 1] += new_right - g_hr[y, x + 1]
        else:
            # Horizontal-direction edge — Eqs. (13) & (14)
            new_below = 0.5 * (g_hr[y + 1, x] + g_hr[y + 2, x])
            new_above = 0.5 * (g_hr[y - 1, x] + g_hr[y - 2, x])
            g_e[y + 1, x] += new_below - g_hr[y + 1, x]
            g_e[y - 1, x] += new_above - g_hr[y - 1, x]

    return g_e


# =========================================================
# Main pipeline  (Figure 2 block diagram)
# =========================================================

def ola_espline_interpolate_single_channel(lr_image, scale_factor,
                                           k=None, use_cs=True,
                                           cs_nests=10, cs_generations=20):
    """
    Full OLA e-spline pipeline for a single greyscale channel.

    Steps (matching Figure 2):
      1. LA filtering  → H_Ab
      2. USM           → G_SLR   (k optimised by CS when use_cs=True)
      3. B-spline interpolation → G_HR
      4. Edge expansion (G_e) + additive fusion → G_RHR  [Eq. 15 fixed]

    Args:
        lr_image     : 2-D uint8 / float input.
        scale_factor : upscaling factor (e.g. 2 or 4).
        k            : gain factor; if None and use_cs=True it is optimised.
        use_cs       : whether to run Cuckoo Search for k.
        cs_nests     : CS population size.
        cs_generations: CS number of generations.

    Returns:
        Upscaled HR image as uint8.
    """
    lr_float = lr_image.astype(np.float64)

    # ------------------------------------------------------------------
    # Step 1 – Local Adaptive filtering
    # ------------------------------------------------------------------
    h_ab = local_adaptive_filter(lr_float)

    # ------------------------------------------------------------------
    # Step 2 – Unsharp Masking with CS-optimised gain k
    # Eq. (4): H(x,y) = G_LR - H_Ab
    # Eq. (1): G_SLR  = G_LR + k * H(x,y)
    # ------------------------------------------------------------------
    h_xy = lr_float - h_ab   # HPF image, Eq. (4)

    if use_cs and k is None:
        # Fitness proxy: sharpness (variance of Laplacian) of the
        # sharpened LR image — maximised when k best restores HF.
        def fitness_fn(k_val):
            g_slr_trial = lr_float + k_val * h_xy
            g_slr_clipped = np.clip(g_slr_trial, 0, 255).astype(np.uint8)
            lap = cv2.Laplacian(g_slr_clipped, cv2.CV_64F)
            return float(lap.var())   # higher variance → sharper image

        k = cuckoo_search(fitness_fn,
                          n_nests=cs_nests,
                          n_generations=cs_generations)
    elif k is None:
        k = 1.5   # default fallback when CS is disabled

    g_slr = lr_float + k * h_xy   # sharpened LR, Eq. (1)

    # ------------------------------------------------------------------
    # Step 3 – B-spline interpolation (cubic, order=3)  Eq. (6)
    # ------------------------------------------------------------------
    g_hr = zoom(g_slr, scale_factor, order=3, mode='reflect')

    # ------------------------------------------------------------------
    # Step 4 – Edge expansion and ADDITIVE fusion  Eq. (15) [FIXED]
    #   G_RHR = G_HR + G_e
    # Previously the code modified G_HR in-place, which skipped the
    # explicit additive step required by Eq. (15).
    # ------------------------------------------------------------------
    g_e   = edge_expansion(g_hr)          # additive correction layer
    g_rhr = g_hr + g_e                    # Eq. (15): G_RHR = G_HR + G_e

    return np.clip(g_rhr, 0, 255).astype(np.uint8)


def ola_espline_interpolate(lr_image, scale_factor=2, k=None,
                            use_cs=True, cs_nests=10, cs_generations=20):
    """
    OLA e-spline upscaling (colour or greyscale).

    Args:
        lr_image      : Input LR image (greyscale or BGR uint8).
        scale_factor  : Upscaling factor (2 or 4 as in the paper).
        k             : USM gain; None → optimised via CS (recommended).
        use_cs        : Enable Cuckoo Search optimisation for k.
        cs_nests      : CS population size (paper uses small values).
        cs_generations: CS iterations.

    Returns:
        HR image (uint8, same channel layout as input).
    """
    is_color = lr_image.ndim == 3

    if is_color:
        channels    = cv2.split(lr_image)
        hr_channels = [
            ola_espline_interpolate_single_channel(
                ch, scale_factor, k=k,
                use_cs=use_cs,
                cs_nests=cs_nests,
                cs_generations=cs_generations
            )
            for ch in channels
        ]
        return cv2.merge(hr_channels)
    else:
        return ola_espline_interpolate_single_channel(
            lr_image, scale_factor, k=k,
            use_cs=use_cs,
            cs_nests=cs_nests,
            cs_generations=cs_generations
        )


# =========================================================
# Example Usage
# =========================================================
if __name__ == "__main__":
    # --- With CS optimisation (recommended, matches paper fully) ---
    lr_img = cv2.imread('lr_image.png')
    hr_img = ola_espline_interpolate(lr_img, scale_factor=4, use_cs=True)
    cv2.imwrite('hr_output_cs.png', hr_img)

    # --- With fixed k (faster, skips CS) ---
    # hr_img = ola_espline_interpolate(lr_img, scale_factor=4, k=1.5, use_cs=False)
    # cv2.imwrite('hr_output_fixed_k.png', hr_img)
    pass
