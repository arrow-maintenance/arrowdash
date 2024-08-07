# Arrow Maintainer Dashboard

Quarto dashboard for simplifying project maintenance and monitoring
important metrics for tracking project sustainability.

<p align="middle">
<img width="90%" alt="Screenshot 2024-08-07 at 07 09 11" src="https://github.com/user-attachments/assets/4256ec07-c9b4-4807-98cd-53be8408e0eb">
</p>

<p align="middle">
  <img width="45%" alt="Screenshot 2024-08-07 at 07 09 23" src="https://github.com/user-attachments/assets/e6a78532-1b19-490a-a9f3-391534de4299">
  <img width="45%" alt="Screenshot 2024-08-07 at 07 09 37" src="https://github.com/user-attachments/assets/b18e48b3-9e09-4547-b72b-04fd1b5d9987">
</p>

## Setup for local development

For local development both Python and R need to be installed.
In an active R session first install `remotes` package:

```r
install.packages("remotes")
```

and from the project root directory (`/arrowdash`) install R
dependencies:

```r
remotes::install_deps()
```

then create Python virtual environment with ``reticulate``:

```r
library(reticulate)
virtualenv_create("r-arrow-dash")
virtualenv_install(requirements="requirements.txt", envname = "r-arrow-dash")
```

This will save the virtual environment named "r-arrow-dash" into the
`.virtualenvs` for Quarto dashboard to find.

Make sure you select the "r-arrow-dash" environment in your terminal with
`source your-path/.virtualenvs/r-arrow-dash/bin/activate`
and export the GitHub access token in the terminal with
`export GH_API_TOKEN=my_token` where `py_token` is your active GitHub token.
