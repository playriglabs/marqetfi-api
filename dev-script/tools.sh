#!/bin/bash

# Development tools script for MarqetFi API
# Usage: ./dev-script/tools.sh [--skip=<step1,step2>]
# Steps: lint, test, build, push

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
SKIP_STEPS=""
IMAGE_NAME="marqetfi-api"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${DOCKER_REGISTRY:-}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip=*)
            SKIP_STEPS="${1#*=}"
            shift
            ;;
        --skip)
            SKIP_STEPS="$2"
            shift 2
            ;;
        --image=*)
            IMAGE_NAME="${1#*=}"
            shift
            ;;
        --tag=*)
            IMAGE_TAG="${1#*=}"
            shift
            ;;
        --registry=*)
            REGISTRY="${1#*=}"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip=<steps>     Skip specific steps (comma-separated: lint,test,build,push)"
            echo "  --image=<name>     Docker image name (default: marqetfi-api)"
            echo "  --tag=<tag>        Docker image tag (default: latest)"
            echo "  --registry=<url>   Docker registry URL (default: from DOCKER_REGISTRY env)"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Run all steps"
            echo "  $0 --skip=lint,test                  # Skip lint and test"
            echo "  $0 --skip=push                       # Skip docker push"
            echo "  $0 --image=myapp --tag=v1.0.0       # Custom image name and tag"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to check if a step should be skipped
should_skip() {
    local step=$1
    if [[ -z "$SKIP_STEPS" ]]; then
        return 1  # Don't skip
    fi

    # Check if step is in skip list (comma-separated or space-separated)
    IFS=',' read -ra SKIP_ARRAY <<< "$SKIP_STEPS"
    for skip_step in "${SKIP_ARRAY[@]}"; do
        if [[ "$skip_step" == "$step" ]]; then
            return 0  # Skip
        fi
    done
    return 1  # Don't skip
}

# Function to print step header
print_step() {
    local step=$1
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}Step: $step${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Function to print success message
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error message
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to print warning message
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Step 1: Lint
run_lint() {
    if should_skip "lint"; then
        print_warning "Skipping lint step"
        return 0
    fi

    print_step "Lint"
    echo "Running linters..."

    if make lint; then
        print_success "Lint passed"
        return 0
    else
        print_error "Lint failed"
        return 1
    fi
}

# Step 2: Test
run_test() {
    if should_skip "test"; then
        print_warning "Skipping test step"
        return 0
    fi

    print_step "Test"
    echo "Running tests..."

    if make test; then
        print_success "Tests passed"
        return 0
    else
        print_error "Tests failed"
        return 1
    fi
}

# Step 3: Build Docker
run_build() {
    if should_skip "build"; then
        print_warning "Skipping build step"
        return 0
    fi

    print_step "Build Docker"

    # Construct full image name
    if [[ -n "$REGISTRY" ]]; then
        FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
    fi

    echo "Building Docker image: $FULL_IMAGE_NAME"

    if docker build -t "$FULL_IMAGE_NAME" .; then
        # Also tag as latest if not already
        if [[ "$IMAGE_TAG" != "latest" ]]; then
            if [[ -n "$REGISTRY" ]]; then
                docker tag "$FULL_IMAGE_NAME" "${REGISTRY}/${IMAGE_NAME}:latest"
            else
                docker tag "$FULL_IMAGE_NAME" "${IMAGE_NAME}:latest"
            fi
        fi
        print_success "Docker image built successfully"
        return 0
    else
        print_error "Docker build failed"
        return 1
    fi
}

# Step 4: Push Docker
run_push() {
    if should_skip "push"; then
        print_warning "Skipping push step"
        return 0
    fi

    print_step "Push Docker"

    # Construct full image name
    if [[ -n "$REGISTRY" ]]; then
        FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
    fi

    echo "Pushing Docker image: $FULL_IMAGE_NAME"

    # Check if image exists locally
    if ! docker image inspect "$FULL_IMAGE_NAME" &> /dev/null; then
        print_error "Image $FULL_IMAGE_NAME not found locally. Run build step first."
        return 1
    fi

    if docker push "$FULL_IMAGE_NAME"; then
        # Also push latest tag if it exists and is different
        if [[ "$IMAGE_TAG" != "latest" ]]; then
            if [[ -n "$REGISTRY" ]]; then
                LATEST_IMAGE="${REGISTRY}/${IMAGE_NAME}:latest"
            else
                LATEST_IMAGE="${IMAGE_NAME}:latest"
            fi

            if docker image inspect "$LATEST_IMAGE" &> /dev/null; then
                echo "Pushing latest tag..."
                docker push "$LATEST_IMAGE"
            fi
        fi
        print_success "Docker image pushed successfully"
        return 0
    else
        print_error "Docker push failed"
        return 1
    fi
}

# Main execution
main() {
    echo -e "${GREEN}"
    echo "╔════════════════════════════════════════╗"
    echo "║   MarqetFi API Development Tools       ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"

    # Show configuration
    echo "Configuration:"
    echo "  Image Name: $IMAGE_NAME"
    echo "  Image Tag: $IMAGE_TAG"
    if [[ -n "$REGISTRY" ]]; then
        echo "  Registry: $REGISTRY"
    else
        echo "  Registry: (none - local only)"
    fi
    if [[ -n "$SKIP_STEPS" ]]; then
        echo "  Skipping: $SKIP_STEPS"
    fi
    echo ""

    # Track if any step failed
    FAILED=0

    # Run steps in order
    if ! run_lint; then
        FAILED=1
    fi

    if ! run_test; then
        FAILED=1
    fi

    if ! run_build; then
        FAILED=1
    fi

    if ! run_push; then
        FAILED=1
    fi

    # Final summary
    echo -e "\n${BLUE}========================================${NC}"
    if [[ $FAILED -eq 0 ]]; then
        echo -e "${GREEN}✅ All steps completed successfully!${NC}"
        exit 0
    else
        echo -e "${RED}❌ Some steps failed. Please check the output above.${NC}"
        exit 1
    fi
}

# Run main function
main
