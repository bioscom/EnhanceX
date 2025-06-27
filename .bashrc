# Set Django project environment
export PROJECT_HOME="/glb/home/ngibe6/enhancex"
export VENV_PATH="$PROJECT_HOME/venv"

# Activate virtual environment automatically when entering the project folder
function cdproj() {
    cd "$PROJECT_HOME" || return
    source "$VENV_PATH/bin/activate"
    echo "Virtual environment activated. Current directory: $(pwd)"
}

# Add Gunicorn and Django commands to PATH (optional)
export PATH="$VENV_PATH/bin:$PATH"

export ODBCSYSINI=$HOME
export ODBCINSTINI=$HOME/.odbcinst.ini
export LD_LIBRARY_PATH=$HOME/opt/opt/microsoft/msodbcsql17/lib64:$LD_LIBRARY_PATH