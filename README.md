# Tutorial Repository

This repository contains various tutorials, each organized into its own folder under the `tutorials/` directory. Each tutorial is a standalone project or script that demonstrates a specific concept or feature. The `run.py` script is provided to easily execute any of these tutorials.

## Repository Structure

- **tutorials/**: This directory contains folders for each tutorial video or topic. Each folder may have its own scripts, data, and resources.

- **run.py**: A utility script designed to simplify running any tutorial script within the repository.

## Prerequisites

Before running the tutorials, make sure you have the following installed:

- Python 3.8 or above
- pip (Python package installer)

## Installation

To install all necessary dependencies for the tutorials, use the following command:

```bash
pip install -r requirements.txt
```

## Running a Tutorial

You can run any tutorial script using the `run.py` script. Here’s how to use it:

### Basic Usage

The `run.py` script requires one argument: the path to the tutorial script you want to run.

```bash
python run.py <path_to_tutorial_script>
```

### Example: Running the "main.py" script in the "tickets" tutorial

```bash
python run.py tutorials/tickets/main.py
```

### Example: Running another tutorial script

```bash
python run.py tutorials/some_other_tutorial/some_script.py
```

Simply replace `<path_to_tutorial_script>` with the relative path to the script you want to execute.


## Contribution

Contributions are not possible.

## License

This project is licensed under the Everyman.AI License 
