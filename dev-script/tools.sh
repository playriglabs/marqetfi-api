#!/bin/bash

# Development tools script for MarqetFi API
# Usage: ./dev-script/tools.sh [--skip=<step1,step2>] [--no-auto-fix]
# Steps: lint, test, build, push

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
SKIP_STEPS=""
IMAGE_NAME="marqetfi-api"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${DOCKER_REGISTRY:-}"
AUTO_FIX=true
MAX_RETRIES=3
LINT_ERRORS_FILE=$(mktemp)
TEST_ERRORS_FILE=$(mktemp)

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
        --no-auto-fix)
            AUTO_FIX=false
            shift
            ;;
        --max-retries=*)
            MAX_RETRIES="${1#*=}"
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
            echo "  --no-auto-fix      Disable automatic fixing of issues (default: auto-fix enabled)"
            echo "  --max-retries=<n>  Maximum retries for flaky operations (default: 3)"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Run all steps with auto-fix"
            echo "  $0 --skip=lint,test                  # Skip lint and test"
            echo "  $0 --no-auto-fix                     # Disable auto-fix"
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

# Function to print info message
print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Docker daemon
check_docker() {
    if ! command_exists docker; then
        print_error "Docker is not installed or not in PATH"
        return 1
    fi

    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running"
        print_info "Please start Docker and try again"
        return 1
    fi
    return 0
}

# Function to check required tools
check_dependencies() {
    local missing=()

    if ! command_exists make; then
        missing+=("make")
    fi

    if ! command_exists python3; then
        missing+=("python3")
    fi

    if ! command_exists pip; then
        missing+=("pip")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        print_error "Missing required tools: ${missing[*]}"
        print_info "Please install the missing tools and try again"
        return 1
    fi

    return 0
}

# Function to retry a command
retry_command() {
    local cmd="$1"
    local description="${2:-Command}"
    local attempt=1

    while [[ $attempt -le $MAX_RETRIES ]]; do
        if eval "$cmd"; then
            return 0
        fi

        if [[ $attempt -lt $MAX_RETRIES ]]; then
            print_warning "$description failed (attempt $attempt/$MAX_RETRIES). Retrying..."
            sleep $((attempt * 2))  # Exponential backoff
        fi

        ((attempt++))
    done

    print_error "$description failed after $MAX_RETRIES attempts"
    return 1
}

# Function to auto-fix linting issues
auto_fix_lint() {
    print_info "Attempting to auto-fix linting issues..."

    # Try ruff auto-fix first (fastest and can fix many issues)
    if command_exists ruff; then
        print_info "Running ruff check --fix..."
        if ruff check --fix app/ tests/ 2>/dev/null; then
            print_success "Ruff auto-fix completed"
        else
            print_warning "Ruff auto-fix had some issues (non-fixable errors may remain)"
        fi
    fi

    # Run make format to fix formatting issues
    if make format 2>/dev/null; then
        print_success "Code formatting applied"
        return 0
    else
        print_warning "Formatting step had issues"
        return 1
    fi
}

# Function to strip ANSI color codes
strip_ansi() {
    sed 's/\x1b\[[0-9;]*m//g'
}

# Function to parse lint errors
parse_lint_errors() {
    local lint_output="$1"
    local errors_file="$2"

    # Clear previous errors
    > "$errors_file"

    # Strip ANSI codes and save to temp file for processing
    local temp_file
    temp_file=$(mktemp)
    echo "$lint_output" | strip_ansi > "$temp_file"

    # Parse ruff errors
    # Format can be:
    #   CODE [*] Message
    #     --> filepath:line:column
    # Or:
    #   CODE --> filepath:line:column
    local prev_line=""
    while IFS= read -r line; do
        # Check if line contains an error code
        if echo "$line" | grep -qE '^[[:space:]]*[A-Z][0-9]+'; then
            # Extract error code (e.g., F821, B904, UP038, E721, I001)
            error_code=$(echo "$line" | grep -oE '[A-Z][0-9]+' | sed -n '1p')

            # Extract error message (text after code, before [*] or end of line)
            error_msg=$(echo "$line" | sed -n 's/.*[A-Z][0-9]\+[[:space:]]*\[.*\][[:space:]]*\(.*\)/\1/p')
            if [[ -z "$error_msg" ]]; then
                error_msg=$(echo "$line" | sed -n 's/.*[A-Z][0-9]\+[[:space:]]*\(.*\)/\1/p' | xargs)
            fi

            # Store for next line processing
            prev_line="$line"
            continue
        fi

        # Check if line contains --> (file path line, usually follows error code line)
        if echo "$line" | grep -qE '[[:space:]]+-->'; then
            # Extract file path (between --> and :)
            file_path=$(echo "$line" | sed -n 's/.*-->[[:space:]]*\([^:]*\):.*/\1/p')

            # If we have a previous line with error code, use it
            if [[ -n "$prev_line" ]]; then
                error_code=$(echo "$prev_line" | grep -oE '[A-Z][0-9]+' | sed -n '1p')
                error_msg=$(echo "$prev_line" | sed -n 's/.*[A-Z][0-9]\+[[:space:]]*\[.*\][[:space:]]*\(.*\)/\1/p')
                if [[ -z "$error_msg" ]]; then
                    error_msg=$(echo "$prev_line" | sed -n 's/.*[A-Z][0-9]\+[[:space:]]*\(.*\)/\1/p' | xargs)
                fi
            fi

            if [[ -n "$error_code" && -n "$file_path" ]]; then
                # Normalize file path
                file_path="${file_path#./}"
                if [[ -z "$error_msg" || "$error_msg" == "$error_code" || -z "$(echo "$error_msg" | xargs)" ]]; then
                    # Use default error message based on code
                    case "$error_code" in
                        I001) error_msg="Import block is un-sorted or un-formatted" ;;
                        F821) error_msg="Undefined name" ;;
                        B904) error_msg="Within an except clause, raise exceptions with raise ... from err" ;;
                        UP038) error_msg="Use X | Y in isinstance call instead of (X, Y)" ;;
                        E721) error_msg="Use isinstance() for type comparisons" ;;
                        *) error_msg="Linting error" ;;
                    esac
                fi
                echo "${file_path}|${error_code}|${error_msg}" >> "$errors_file"
            fi
            prev_line=""
        fi
    done < "$temp_file"

    # Capture isort errors (format: ERROR: /path/to/file.py)
    while IFS= read -r line; do
        if echo "$line" | grep -qE "ERROR:.*\.py|Imports are incorrectly"; then
            # Try multiple patterns to extract file path
            file_path=$(echo "$line" | grep -oE '/[^[:space:]]+\.py' | sed -n '1p')
            if [[ -z "$file_path" ]]; then
                # Try extracting from ERROR: line
                file_path=$(echo "$line" | sed -n 's/.*ERROR:[[:space:]]*\([^[:space:]]*\.py\).*/\1/p')
            fi
            if [[ -z "$file_path" ]]; then
                # Try extracting relative path
                file_path=$(echo "$line" | grep -oE '[^[:space:]]+\.py' | sed -n '1p')
            fi
            if [[ -n "$file_path" ]]; then
                file_path="${file_path#./}"
                echo "${file_path}|I001|Import block is un-sorted or un-formatted" >> "$errors_file"
            fi
        fi
    done < "$temp_file"

    # Cleanup temp file
    rm -f "$temp_file"

    # Remove duplicates and sort
    if [[ -f "$errors_file" ]] && [[ -s "$errors_file" ]]; then
        sort -u "$errors_file" > "${errors_file}.tmp" && mv "${errors_file}.tmp" "$errors_file"
    fi
}

# Step 1: Lint
run_lint() {
    if should_skip "lint"; then
        print_warning "Skipping lint step"
        return 0
    fi

    print_step "Lint"
    echo "Running linters..."

    local lint_output
    lint_output=$(make lint 2>&1)
    local lint_status=$?

    if [[ $lint_status -eq 0 ]]; then
        print_success "Lint passed"
        > "$LINT_ERRORS_FILE"  # Clear errors
        return 0
    else
        print_warning "Lint failed"

        # Parse and store errors
        parse_lint_errors "$lint_output" "$LINT_ERRORS_FILE"

        # Show error summary immediately
        show_lint_error_summary

        if [[ "$AUTO_FIX" == "true" ]]; then
            print_info "Auto-fix is enabled. Attempting to fix issues..."
            if auto_fix_lint; then
                print_info "Re-running linters after auto-fix..."
                lint_output=$(make lint 2>&1)
                lint_status=$?
                if [[ $lint_status -eq 0 ]]; then
                    print_success "Lint passed after auto-fix"
                    > "$LINT_ERRORS_FILE"  # Clear errors
                    return 0
                else
                    print_error "Lint still failing after auto-fix. Manual intervention required."
                    parse_lint_errors "$lint_output" "$LINT_ERRORS_FILE"
                    show_lint_error_summary
                    return 1
                fi
            else
                print_error "Auto-fix failed or couldn't fix all issues"
                return 1
            fi
        else
            print_error "Lint failed. Run with auto-fix enabled or fix issues manually."
            print_info "Tip: Run 'make format' to fix formatting issues"
            return 1
        fi
    fi
}

# Function to parse test errors
parse_test_errors() {
    local test_output="$1"
    local errors_file="$2"

    # Clear previous errors
    > "$errors_file"

    # Parse pytest errors (format: filepath::test_name)
    echo "$test_output" | grep -E "FAILED|ERROR" | grep -E "\.py::" | while IFS= read -r line; do
        # Extract file path and test name
        file_path=$(echo "$line" | grep -oE '[^[:space:]]+\.py::[^[:space:]]+' | sed -n '1p')
        error_type=$(echo "$line" | grep -oE "(FAILED|ERROR)" | sed -n '1p')

        if [[ -n "$file_path" && -n "$error_type" ]]; then
            echo "${file_path}|${error_type}|Test failure" >> "$errors_file"
        fi
    done

    # Also capture import errors
    echo "$test_output" | grep -E "ImportError|ModuleNotFoundError" | while IFS= read -r line; do
        file_path=$(echo "$line" | grep -oE '/[^[:space:]]+\.py' | sed -n '1p')
        error_msg=$(echo "$line" | grep -oE "(ImportError|ModuleNotFoundError):.*" | sed -n '1p')
        if [[ -n "$file_path" && -n "$error_msg" ]]; then
            echo "${file_path}|ImportError|${error_msg}" >> "$errors_file"
        fi
    done
}

# Step 2: Test
run_test() {
    if should_skip "test"; then
        print_warning "Skipping test step"
        return 0
    fi

    print_step "Test"
    echo "Running tests..."

    # Check if pytest is available
    if ! command_exists pytest && ! python3 -m pytest --version >/dev/null 2>&1; then
        print_warning "pytest not found. Installing test dependencies..."
        if pip install -q -r requirements-dev.txt 2>/dev/null; then
            print_success "Test dependencies installed"
        else
            print_error "Failed to install test dependencies"
            return 1
        fi
    fi

    # Capture test output for error parsing
    local test_output
    local test_status=0

    # Run tests and capture output
    test_output=$(make test 2>&1)
    test_status=$?

    if [[ $test_status -eq 0 ]]; then
        print_success "Tests passed"
        > "$TEST_ERRORS_FILE"  # Clear errors
        return 0
    else
        # Parse and store errors
        parse_test_errors "$test_output" "$TEST_ERRORS_FILE"

        # Show error summary immediately
        show_test_error_summary

        # Retry if enabled
        local attempt=1
        while [[ $attempt -lt $MAX_RETRIES && $test_status -ne 0 ]]; do
            print_warning "Tests failed (attempt $attempt/$MAX_RETRIES). Retrying..."
            sleep $((attempt * 2))
            test_output=$(make test 2>&1)
            test_status=$?
            if [[ $test_status -eq 0 ]]; then
                print_success "Tests passed"
                > "$TEST_ERRORS_FILE"  # Clear errors
                return 0
            fi
            parse_test_errors "$test_output" "$TEST_ERRORS_FILE"
            ((attempt++))
        done

        print_error "Tests failed after $MAX_RETRIES attempts"
        show_test_error_summary
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

    # Check Docker availability
    if ! check_docker; then
        return 1
    fi

    # Check if Dockerfile exists
    if [[ ! -f Dockerfile ]]; then
        print_error "Dockerfile not found in current directory"
        return 1
    fi

    # Construct full image name
    if [[ -n "$REGISTRY" ]]; then
        FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
    fi

    echo "Building Docker image: $FULL_IMAGE_NAME"

    # Retry build in case of network issues
    if retry_command "docker build -t \"$FULL_IMAGE_NAME\" ." "Docker build"; then
        # Also tag as latest if not already
        if [[ "$IMAGE_TAG" != "latest" ]]; then
            if [[ -n "$REGISTRY" ]]; then
                docker tag "$FULL_IMAGE_NAME" "${REGISTRY}/${IMAGE_NAME}:latest" 2>/dev/null || true
            else
                docker tag "$FULL_IMAGE_NAME" "${IMAGE_NAME}:latest" 2>/dev/null || true
            fi
        fi
        print_success "Docker image built successfully"
        return 0
    else
        print_error "Docker build failed after $MAX_RETRIES attempts"
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

    # Check Docker availability
    if ! check_docker; then
        return 1
    fi

    # Construct full image name
    if [[ -n "$REGISTRY" ]]; then
        FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
    fi

    echo "Pushing Docker image: $FULL_IMAGE_NAME"

    # Check if image exists locally
    if ! docker image inspect "$FULL_IMAGE_NAME" &> /dev/null; then
        print_error "Image $FULL_IMAGE_NAME not found locally."
        if [[ "$AUTO_FIX" == "true" ]]; then
            print_info "Attempting to build image first..."
            if run_build; then
                print_info "Build successful, continuing with push..."
            else
                print_error "Build failed. Cannot push."
                return 1
            fi
        else
            print_error "Run build step first or enable auto-fix."
            return 1
        fi
    fi

    # Check registry authentication if registry is specified
    if [[ -n "$REGISTRY" ]]; then
        print_info "Checking registry authentication..."
        if ! docker login "$REGISTRY" >/dev/null 2>&1; then
            print_warning "Registry authentication may be required"
            print_info "You may need to run: docker login $REGISTRY"
        fi
    fi

    # Retry push in case of network issues
    if retry_command "docker push \"$FULL_IMAGE_NAME\"" "Docker push"; then
        # Also push latest tag if it exists and is different
        if [[ "$IMAGE_TAG" != "latest" ]]; then
            if [[ -n "$REGISTRY" ]]; then
                LATEST_IMAGE="${REGISTRY}/${IMAGE_NAME}:latest"
            else
                LATEST_IMAGE="${IMAGE_NAME}:latest"
            fi

            if docker image inspect "$LATEST_IMAGE" &> /dev/null; then
                echo "Pushing latest tag..."
                retry_command "docker push \"$LATEST_IMAGE\"" "Docker push (latest tag)" || true
            fi
        fi
        print_success "Docker image pushed successfully"
        return 0
    else
        print_error "Docker push failed after $MAX_RETRIES attempts"
        if [[ -n "$REGISTRY" ]]; then
            print_info "Tip: Ensure you're authenticated: docker login $REGISTRY"
        fi
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

    # Pre-flight checks
    print_info "Running pre-flight checks..."
    if ! check_dependencies; then
        exit 1
    fi

    # Check Docker only if build or push steps are not skipped
    if ! should_skip "build" || ! should_skip "push"; then
        if ! check_docker; then
            print_error "Docker checks failed. Build/push steps will fail."
            exit 1
        fi
    else
        print_info "Docker checks skipped (build and push are skipped)"
    fi
    print_success "Pre-flight checks passed"

    # Show configuration
    echo ""
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
    echo "  Auto-fix: $AUTO_FIX"
    echo "  Max retries: $MAX_RETRIES"
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

    # Generate error summary
    generate_error_summary

    # Final summary
    echo -e "\n${BLUE}========================================${NC}"
    if [[ $FAILED -eq 0 ]]; then
        echo -e "${GREEN}✅ All steps completed successfully!${NC}"
        # Cleanup temp files
        rm -f "$LINT_ERRORS_FILE" "$TEST_ERRORS_FILE"
        exit 0
    else
        echo -e "${RED}❌ Some steps failed. Please check the output above.${NC}"
        echo ""
        print_info "Troubleshooting tips:"
        echo "  - Run with --no-auto-fix to see original errors"
        echo "  - Check that all dependencies are installed: make dev"
        echo "  - Ensure Docker is running for build/push steps"
        echo "  - Review error messages above for specific issues"
        # Cleanup temp files
        rm -f "$LINT_ERRORS_FILE" "$TEST_ERRORS_FILE"
        exit 1
    fi
}

# Function to show lint error summary
show_lint_error_summary() {
    if [[ ! -f "$LINT_ERRORS_FILE" ]] || [[ ! -s "$LINT_ERRORS_FILE" ]]; then
        return 0
    fi

    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Linting Error Summary${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    # Group errors by file using sort and awk
    local grouped_errors
    grouped_errors=$(sort -t'|' -k1 "$LINT_ERRORS_FILE" | awk -F'|' '
    {
        file = $1
        code = $2
        if (file != "" && code != "") {
            if (files[file] == "") {
                files[file] = code
            } else {
                files[file] = files[file] ", " code
            }
        }
    }
    END {
        for (file in files) {
            print file "|" files[file]
        }
    }' | sort)

    # Display errors grouped by file
    echo "$grouped_errors" | while IFS='|' read -r file_path error_codes; do
        if [[ -n "$file_path" && -n "$error_codes" ]]; then
            echo -e "  ${CYAN}📄${NC} ${CYAN}$file_path${NC}"
            echo -e "     ${RED}❌${NC} ${RED}$error_codes${NC}"
            echo ""
        fi
    done

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Function to show test error summary
show_test_error_summary() {
    if [[ ! -f "$TEST_ERRORS_FILE" ]] || [[ ! -s "$TEST_ERRORS_FILE" ]]; then
        return 0
    fi

    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Test Error Summary${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

    # Group errors by file using sort and awk
    local grouped_test_errors
    grouped_test_errors=$(sort -t'|' -k1 "$TEST_ERRORS_FILE" | awk -F'|' '
    {
        # Extract just the file path (before ::)
        file = $1
        sub(/::.*/, "", file)
        error_type = $2
        if (file != "" && error_type != "") {
            if (files[file] == "") {
                files[file] = error_type
            } else {
                files[file] = files[file] ", " error_type
            }
        }
    }
    END {
        for (file in files) {
            print file "|" files[file]
        }
    }' | sort)

    # Display errors grouped by file
    echo "$grouped_test_errors" | while IFS='|' read -r file_path error_types; do
        if [[ -n "$file_path" && -n "$error_types" ]]; then
            # Normalize file path
            file_path="${file_path#./}"
            echo -e "  ${CYAN}📄${NC} ${CYAN}$file_path${NC}"
            echo -e "     ${RED}❌${NC} ${RED}$error_types${NC}"
            echo ""
        fi
    done

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Function to generate error summary
generate_error_summary() {
    local has_errors=0

    # Check if we have any errors
    if [[ -f "$LINT_ERRORS_FILE" ]] && [[ -s "$LINT_ERRORS_FILE" ]]; then
        has_errors=1
    fi
    if [[ -f "$TEST_ERRORS_FILE" ]] && [[ -s "$TEST_ERRORS_FILE" ]]; then
        has_errors=1
    fi

    if [[ $has_errors -eq 0 ]]; then
        return 0
    fi

    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}Error Summary${NC}"
    echo -e "${BLUE}========================================${NC}\n"

    # Process lint errors
    if [[ -f "$LINT_ERRORS_FILE" ]] && [[ -s "$LINT_ERRORS_FILE" ]]; then
        echo -e "${YELLOW}Linting Errors:${NC}"
        echo ""

        # Group errors by file using sort and awk
        local grouped_errors
        grouped_errors=$(sort -t'|' -k1 "$LINT_ERRORS_FILE" | awk -F'|' '
        {
            file = $1
            code = $2
            if (file != "" && code != "") {
                if (files[file] == "") {
                    files[file] = code
                } else {
                    files[file] = files[file] ", " code
                }
            }
        }
        END {
            for (file in files) {
                print file "|" files[file]
            }
        }' | sort)

        # Display errors grouped by file
        echo "$grouped_errors" | while IFS='|' read -r file_path error_codes; do
            if [[ -n "$file_path" && -n "$error_codes" ]]; then
                echo -e "  ${CYAN}File:${NC} $file_path"
                echo -e "    ${RED}Rules:${NC} $error_codes"
                echo ""
            fi
        done
    fi

    # Process test errors
    if [[ -f "$TEST_ERRORS_FILE" ]] && [[ -s "$TEST_ERRORS_FILE" ]]; then
        echo -e "${YELLOW}Test Errors:${NC}"
        echo ""

        # Group errors by file using sort and awk
        local grouped_test_errors
        grouped_test_errors=$(sort -t'|' -k1 "$TEST_ERRORS_FILE" | awk -F'|' '
        {
            # Extract just the file path (before ::)
            file = $1
            sub(/::.*/, "", file)
            error_type = $2
            if (file != "" && error_type != "") {
                if (files[file] == "") {
                    files[file] = error_type
                } else {
                    files[file] = files[file] ", " error_type
                }
            }
        }
        END {
            for (file in files) {
                print file "|" files[file]
            }
        }' | sort)

        # Display errors grouped by file
        echo "$grouped_test_errors" | while IFS='|' read -r file_path error_types; do
            if [[ -n "$file_path" && -n "$error_types" ]]; then
                # Normalize file path
                file_path="${file_path#./}"
                echo -e "  ${CYAN}File:${NC} $file_path"
                echo -e "    ${RED}Errors:${NC} $error_types"
                echo ""
            fi
        done
    fi

    echo -e "${BLUE}========================================${NC}\n"
}

# Run main function
main
