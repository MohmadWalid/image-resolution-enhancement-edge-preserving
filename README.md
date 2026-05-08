# Image Resolution Enhancement Using Optimized Edge-Preserving Interpolation

A comparative study of image super-resolution techniques that upscale low-resolution images while preserving edge sharpness and texture details.

## Overview
This project implements and compares multiple interpolation methods for image resolution enhancement:
- Bilinear Interpolation (baseline)
- Bicubic Interpolation
- Lanczos Interpolation
- Optimized Edge-Preserving Method (using B-spline + Cuckoo Search)

Designed for applications in medical imaging, satellite imaging, surveillance, and multimedia.

## Evaluation
- **Datasets:** Set5, Set14, standard test images (Lena, Barbara, Baby, Face, Airplane)
- **Scaling Factors:** ×2, ×4
- **Metrics:** PSNR, SSIM, FSIM
