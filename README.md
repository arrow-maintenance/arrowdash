# Arrow Maintainer Dashboard

Quarto dashboard for simplifying project maintenance and monitoring important metrics for tracking project sustainability.

## Virtual environment

For local development both Python and R need to be installed.

In an active R session, run the following commands to install the dependencies:

```r
install.packages(c("DT", "dplyr", "ggplot2", "knitr", "purrr", "reticulate", "rmarkdown", "stringr", "tibble", "tidyr"))
```

and create a virtual environment with ``reticulate`` (from arrowdash folder):

```r
library(reticulate)
virtualenv_create("r-arrow-dash")
virtualenv_install(requirements="requirements.txt", envname = "r-arrow-dash")
```

This will save the virtual environment named "r-arrow-dash" into the `.virtualenvs` so that the Quarto dashboard can find needed dependencies.