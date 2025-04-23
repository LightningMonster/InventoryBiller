#!/bin/bash
echo "Building BillingApp executable..."
pyinstaller --clean billing_app.spec
echo "Build complete!"
echo "The executable is located in the dist folder."