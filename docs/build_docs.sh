#!/bin/bash

# Script to build U-Probe documentation locally
# Usage: ./build_docs.sh [clean]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building U-Probe Documentation${NC}"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "source/conf.py" ]; then
    echo -e "${RED}Error: Please run this script from the docs/ directory${NC}"
    exit 1
fi

# Clean build if requested
if [ "$1" = "clean" ]; then
    echo -e "${YELLOW}Cleaning previous build...${NC}"
    rm -rf build/
fi

# Create build directory
mkdir -p build

# Check for required packages
echo -e "${YELLOW}Checking dependencies...${NC}"
python -c "import sphinx; print(f'Sphinx version: {sphinx.__version__}')" || {
    echo -e "${RED}Error: Sphinx not found. Install with: pip install -r requirements.txt${NC}"
    exit 1
}

python -c "import sphinx_rtd_theme; print('RTD theme: OK')" || {
    echo -e "${RED}Error: sphinx_rtd_theme not found. Install with: pip install sphinx_rtd_theme${NC}"
    exit 1
}

# Build HTML documentation
echo -e "${YELLOW}Building HTML documentation...${NC}"
sphinx-build -W --keep-going -b html source build/html

# Check for build warnings/errors
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Documentation built successfully!${NC}"
    echo -e "📖 Open ${GREEN}build/html/index.html${NC} in your browser"
    
    # Optionally open in browser (uncomment for automatic opening)
    # if command -v xdg-open > /dev/null; then
    #     xdg-open build/html/index.html
    # elif command -v open > /dev/null; then
    #     open build/html/index.html
    # fi
else
    echo -e "${RED}❌ Documentation build failed!${NC}"
    exit 1
fi

# Build PDF if requested
if [ "$1" = "pdf" ] || [ "$2" = "pdf" ]; then
    echo -e "${YELLOW}Building PDF documentation...${NC}"
    sphinx-build -b latex source build/latex
    
    if [ $? -eq 0 ]; then
        cd build/latex
        make
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ PDF documentation built successfully!${NC}"
            echo -e "📄 PDF location: ${GREEN}build/latex/U-Probe.pdf${NC}"
        else
            echo -e "${RED}❌ PDF build failed!${NC}"
        fi
        cd ../..
    fi
fi

# Show build statistics
echo
echo "Build Statistics:"
echo "=================="
echo "HTML files: $(find build/html -name "*.html" | wc -l)"
echo "Total size: $(du -sh build/html 2>/dev/null | cut -f1)"

# Check for common issues
echo
echo "Health Check:"
echo "============="

# Check for broken internal links
echo -n "Internal links: "
if sphinx-build -W -b linkcheck source build/linkcheck > /dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}Some issues found (check build/linkcheck/output.txt)${NC}"
fi

# Check for missing references
echo -n "References: "
if grep -r "WARNING.*undefined label" build/html > /dev/null 2>&1; then
    echo -e "${YELLOW}Some undefined references found${NC}"
else
    echo -e "${GREEN}OK${NC}"
fi

echo
echo -e "${GREEN}Documentation build complete!${NC}"
echo -e "Next steps:"
echo -e "  1. Review the documentation at ${GREEN}build/html/index.html${NC}"
echo -e "  2. Check for any warnings in the build output"
echo -e "  3. Test navigation and links"
echo -e "  4. Deploy to ReadTheDocs when ready"
