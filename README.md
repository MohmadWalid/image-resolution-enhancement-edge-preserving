# Image Resolution Enhancement Using Optimized Edge-Preserving Interpolation

A comparative study of image super-resolution techniques that upscale low-resolution images while preserving edge sharpness and texture details.

## Team Members
- Aliaa Maamoun Ibrahim (120220255)
- Sama Ayman Bakry (120220342)
- Ahmed Mohamed Ahmed (120220150)
- Mohamed Hamdy Gaber (120220033)
- Youssef Abd El Mohsen Eissa (120220051)
- Mohamed Walid (120220050)

## Overview
This project implements and compares multiple interpolation methods for image resolution enhancement:
- **Bilinear Interpolation** (baseline)
- **Bicubic Interpolation**
- **Lanczos Interpolation**
- **Optimized Edge-Preserving Method** (using B-spline + Cuckoo Search)

## Repository Structure

```
image-resolution-enhancement/
├── README.md
├── notebooks/
│   ├── bilinear_interpolation.ipynb       # Bilinear method implementation
│   ├── bicubic_interpolation.ipynb        # Bicubic method implementation
│   ├── lanczos_interpolation.ipynb        # Lanczos method implementation
│   └── optimized_edge_preserving.ipynb    # Proposed method implementation
├── results/
│   ├── bilinear/
│   │   ├── bilinear_results.csv           # Metrics for bilinear method
│   │   └── sample_outputs/                # Sample comparison images
│   ├── bicubic/
│   │   ├── bicubic_results.csv
│   │   └── sample_outputs/
│   ├── lanczos/
│   │   ├── lanczos_results.csv
│   │   └── sample_outputs/
│   ├── optimized/
│   │   ├── optimized_results.csv
│   │   └── sample_outputs/
│   └── final_comparison.csv               # Combined results from all methods
└── docs/
    └── project_proposal.pdf               # Original project proposal
```

### 📁 How to Upload Your Work

Each team member should upload their files following this structure:

1. **Upload your notebook:**
   - Go to `notebooks/` folder
   - Click "Add file" → "Upload files"
   - Upload your `.ipynb` file with your method name

2. **Upload your results:**
   - Create a folder named after your method in `results/`
   - Upload your CSV file with metrics
   - Upload 2-3 sample output images in `sample_outputs/` subfolder

3. **File naming convention:**
   - Notebook: `{method}_interpolation.ipynb` (e.g., `bicubic_interpolation.ipynb`)
   - Results: `{method}_results.csv` (e.g., `bicubic_results.csv`)
   - Images: `{imagename}_{method}_x{scale}.png` (e.g., `lena_bicubic_x2.png`)

## Evaluation

- **Datasets:** Set5, Set14, standard test images (Lena, Barbara, Baby, Face, Airplane)
- **Scaling Factors:** ×2, ×4
- **Metrics:** PSNR (Peak Signal-to-Noise Ratio), SSIM (Structural Similarity Index), FSIM (Feature Similarity Index)

## How to Run

1. Open any notebook in Google Colab
2. Click "Runtime" → "Run all"
3. Results will be generated automatically
4. Download the CSV files and sample images

