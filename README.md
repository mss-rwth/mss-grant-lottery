# MSS Grant Lottery

A web application for running a weighted lottery to select grant applicants. Built with [Shiny for Python](https://shiny.posit.co/py/) and deployed as a static site via [Shinylive](https://shiny.posit.co/py/docs/shinylive.html).

## How it works

1. Upload an Excel file (`.xlsx` / `.xls`) containing the applicant list
2. Select the column with applicant names and the column with scores (used as selection weights)
3. Choose how many applicants to select
4. Click **Select Applicant(s)** — winners are drawn by weighted random sampling without replacement
5. Download the result as a `.txt` file

## Deployment

The app is automatically exported and deployed to GitLab Pages on every push to `main`.

## Developed by

Alan Correa & Julia Kowalski — MSS, RWTH Aachen University
