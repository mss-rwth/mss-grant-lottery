# MSS Grant Lottery

[![Tests](https://github.com/mss-rwth/mss-grant-lottery/actions/workflows/test.yml/badge.svg)](https://github.com/mss-rwth/mss-grant-lottery/actions/workflows/test.yml)

A web application for a weighted lottery to select grant applicants, inspired by the idea behind [importance sampling](https://en.wikipedia.org/wiki/Importance_sampling): every eligible applicant has a place in the draw, while stronger alignment with the programme objectives increases an applicant's odds of selection. 

Built with [Shiny for Python](https://shiny.posit.co/py/) and deployed as a static site via [Shinylive](https://shiny.posit.co/py/docs/shinylive.html).

## How it works

1. Upload an Excel file (`.xlsx` / `.xls`) containing the applicant list
2. Select the column with applicant names and the column with scores (used as selection weights)
3. Choose how many applicants to select
4. Click **Select Applicant(s)** — winners are drawn by weighted random sampling without replacement
5. Download the result as a `.txt` file

## Deployment

The app is automatically exported and deployed to GitHub Pages on every push to `main`.

## Developed by

[Alan Correa](https://github.com/thealanjason) — MBD, RWTH Aachen University
