#!/usr/bin/env bash

################################################################################
# Escrow Smart Contract Deployment Script
# Updated for: ~/lumiere/smart_contracts/ structure
################################################################################

set -euo pipefail

# Color codes
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Default values
ENVIRONMENT=""
UPGRADE_MODE=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
LOG_DIR="${SCRIPT_DIR}/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/deploy_${TIMESTAMP}.log"

################################################################################
# Helper Functions
################################################################################

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "${LOG_FILE}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "${LOG_FILE}"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "${LOG_FILE}"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "${LOG_FILE}"
}

usage() {
    cat << USAGE
Usage: $0 --environment <dev|prod> [--upgrade]

Options:
    --environment, -e    Deployment environment (dev or prod)
    --upgrade, -u        Upgrade existing program
    --help, -h           Show this help

Examples:
    $0 --environment dev
    $0 --environment prod --upgrade

USAGE
    exit 0
}

check_dependencies() {
    print_info "Checking dependencies..."

    local missing_deps=()

    if ! command -v anchor &> /dev/null; then
        missing_deps+=("anchor")
    fi

    if ! command -v solana &> /dev/null; then
        missing_deps+=("solana")
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        exit 1
    fi

    print_success "All dependencies found"
}

setup_directories() {
    print_info "Setting up directories..."
    mkdir -p "${BUILD_DIR}"
    mkdir -p "${LOG_DIR}"
    print_success "Directories created"
}

setup_keypair() {
    print_info "Checking Solana keypair..."

    local keypair_path
    keypair_path=$(solana config get | grep "Keypair Path" | awk '{print $3}')

    if [ -z "${keypair_path}" ]; then
        keypair_path="/root/.config/solana/id.json"
    fi

    if [ ! -f "${keypair_path}" ]; then
        print_warning "No keypair found at ${keypair_path}"
        print_info "Creating new keypair..."

        mkdir -p "$(dirname "${keypair_path}")"

        if solana-keygen new --no-bip39-passphrase --outfile "${keypair_path}" 2>&1 | tee -a "${LOG_FILE}"; then
            print_success "New keypair created"
            
            local pubkey
            pubkey=$(solana-keygen pubkey "${keypair_path}")
            print_info "Public key: ${pubkey}"
            
            echo "${pubkey}" > "${BUILD_DIR}/deployer_pubkey.txt"
            
            print_warning "⚠️  IMPORTANT: Backup your keypair!"
            print_warning "Location: ${keypair_path}"
        else
            print_error "Failed to create keypair"
            exit 1
        fi
    else
        print_success "Keypair found at ${keypair_path}"
        
        local pubkey
        pubkey=$(solana-keygen pubkey "${keypair_path}")
        print_info "Public key: ${pubkey}"
    fi
}

configure_solana() {
    local env=$1
    local cluster_url

    print_info "Configuring Solana CLI for ${env} environment..."

    case "${env}" in
        dev)
            cluster_url="https://api.devnet.solana.com"
            ;;
        prod)
            cluster_url="https://api.mainnet-beta.solana.com"
            print_warning "⚠️  DEPLOYING TO MAINNET - THIS IS PRODUCTION!"
            read -p "Continue? (yes/no): " confirm
            if [[ "${confirm}" != "yes" ]]; then
                print_info "Cancelled by user"
                exit 0
            fi
            ;;
        *)
            print_error "Invalid environment: ${env}"
            exit 1
            ;;
    esac

    solana config set --url "${cluster_url}"
    print_success "Solana CLI configured to ${cluster_url}"
}

check_balance() {
    local env=$1
    print_info "Checking wallet balance..."

    local balance
    balance=$(solana balance 2>&1 || echo "0")
    print_info "Current balance: ${balance}"

    local numeric_balance
    numeric_balance=$(echo "${balance}" | grep -oE '[0-9]+(\.[0-9]+)?' | head -1 || echo "0")

    local min_balance=2

    if (( $(echo "${numeric_balance} < ${min_balance}" | bc -l) )); then
        print_warning "Low balance detected: ${balance}"

        if [[ "${env}" == "dev" ]]; then
            print_info "Environment is devnet - attempting airdrop..."
            
            local airdrop_amount=4
            local max_retries=3
            local retry_count=0

            while [[ ${retry_count} -lt ${max_retries} ]]; do
                print_info "Requesting ${airdrop_amount} SOL airdrop (attempt $((retry_count + 1))/${max_retries})..."

                if solana airdrop ${airdrop_amount} 2>&1 | tee -a "${LOG_FILE}"; then
                    sleep 3
                    local new_balance
                    new_balance=$(solana balance 2>&1 || echo "0")
                    print_success "Airdrop successful! New balance: ${new_balance}"
                    return 0
                else
                    retry_count=$((retry_count + 1))
                    if [[ ${retry_count} -lt ${max_retries} ]]; then
                        print_warning "Airdrop failed, retrying in 5 seconds..."
                        sleep 5
                    fi
                fi
            done

            print_error "Airdrop failed after ${max_retries} attempts"
            print_error "Request SOL manually: https://faucet.solana.com/"
            print_error "Your wallet: $(solana address)"
            exit 1
        else
            print_error "Insufficient balance for mainnet deployment"
            print_error "Please fund your wallet: $(solana address)"
            exit 1
        fi
    else
        print_success "Balance sufficient: ${balance}"
    fi
}

build_program() {
    print_info "Building Anchor program..."

    cd "${SCRIPT_DIR}"

    if [ -d "${BUILD_DIR}" ]; then
        print_info "Cleaning previous build artifacts..."
        rm -f "${BUILD_DIR}"/*.so "${BUILD_DIR}"/*.json
    fi

    if anchor build 2>&1 | tee -a "${LOG_FILE}"; then
        print_success "Program built successfully"
    else
        print_error "Build failed"
        exit 1
    fi

    # Verify build artifacts exist
    local program_file="${SCRIPT_DIR}/target/deploy/escrow.so"
    if [ ! -f "${program_file}" ]; then
        print_error "Build artifact not found: ${program_file}"
        exit 1
    fi

    # Copy artifacts to build directory
    cp "${program_file}" "${BUILD_DIR}/"
    
    local keypair_file="${SCRIPT_DIR}/target/deploy/escrow-keypair.json"
    if [ -f "${keypair_file}" ]; then
        cp "${keypair_file}" "${BUILD_DIR}/"
    fi

    print_success "Build artifacts copied to ${BUILD_DIR}"
}

get_program_id() {
    local keypair_file="${SCRIPT_DIR}/target/deploy/escrow-keypair.json"

    if [ ! -f "${keypair_file}" ]; then
        print_error "Program keypair not found: ${keypair_file}"
        exit 1
    fi

    solana-keygen pubkey "${keypair_file}"
}

deploy_new() {
    print_info "Deploying new program..."

    if anchor deploy 2>&1 | tee -a "${LOG_FILE}"; then
        local program_id
        program_id=$(get_program_id)

        print_success "Program deployed successfully!"
        print_info "Program ID: ${program_id}"

        # Save program ID
        echo "${program_id}" > "${BUILD_DIR}/program_id.txt"
        echo "PROGRAM_ID=${program_id}" > "${BUILD_DIR}/program_env.sh"

        return 0
    else
        print_error "Deployment failed"
        return 1
    fi
}

upgrade_program() {
    print_info "Upgrading existing program..."

    local program_id
    program_id=$(get_program_id)

    print_info "Program ID: ${program_id}"

    # Verify program exists on-chain
    if ! solana program show "${program_id}" &> /dev/null; then
        print_error "Program ${program_id} not found on-chain"
        print_info "Use deploy without --upgrade flag for new deployment"
        exit 1
    fi

    print_info "Existing program found, proceeding with upgrade..."

    if anchor upgrade target/deploy/escrow.so --program-id "${program_id}" 2>&1 | tee -a "${LOG_FILE}"; then
        print_success "Program upgraded successfully!"
        return 0
    else
        print_error "Upgrade failed"
        return 1
    fi
}

verify_deployment() {
    local program_id=$1

    print_info "Verifying deployment..."

    if solana program show "${program_id}" 2>&1 | tee -a "${LOG_FILE}"; then
        print_success "Deployment verified!"
        return 0
    else
        print_error "Verification failed"
        return 1
    fi
}

generate_summary() {
    local program_id=$1
    local env=$2
    local mode=$3

    local summary_file="${BUILD_DIR}/deployment_summary_${TIMESTAMP}.txt"

    cat > "${summary_file}" << SUMMARY
================================================================================
ESCROW SMART CONTRACT DEPLOYMENT SUMMARY
================================================================================

Timestamp:      ${TIMESTAMP}
Environment:    ${env}
Mode:           ${mode}
Program ID:     ${program_id}
Cluster:        $(solana config get | grep "RPC URL" | awk '{print $3}')
Deployer:       $(solana address)
Log File:       ${LOG_FILE}

Build Artifacts:
    ${BUILD_DIR}/escrow.so
    ${BUILD_DIR}/escrow-keypair.json
    ${BUILD_DIR}/program_id.txt

Solana Explorer:
    https://explorer.solana.com/address/${program_id}?cluster=$([ "${env}" = "dev" ] && echo "devnet" || echo "mainnet")

Next Steps:
    1. Update declare_id! in programs/escrow/src/lib.rs:
       declare_id!("${program_id}");
    
    2. Rebuild program:
       cd ~/lumiere/smart_contracts
       anchor build
    
    3. Upload IDL to chain:
       anchor idl init ${program_id} --filepath target/idl/escrow.json
    
    4. Run tests:
       anchor test --skip-local-validator
    
    5. Update frontend config with Program ID

================================================================================
SUMMARY

    cat "${summary_file}"
    print_success "Deployment summary saved to ${summary_file}"
}

################################################################################
# Main Execution
################################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -u|--upgrade)
                UPGRADE_MODE=true
                shift
                ;;
            -h|--help)
                usage
                ;;
            *)
                print_error "Unknown option: $1"
                usage
                ;;
        esac
    done

    # Validate required arguments
    if [ -z "${ENVIRONMENT}" ]; then
        print_error "Environment is required"
        usage
    fi

    if [[ "${ENVIRONMENT}" != "dev" && "${ENVIRONMENT}" != "prod" ]]; then
        print_error "Environment must be 'dev' or 'prod'"
        exit 1
    fi

    # Start deployment
    print_info "=========================================="
    print_info "Escrow Smart Contract Deployment"
    print_info "=========================================="
    print_info "Environment: ${ENVIRONMENT}"
    print_info "Mode: $([ "${UPGRADE_MODE}" = true ] && echo "UPGRADE" || echo "NEW DEPLOYMENT")"
    print_info "Timestamp: ${TIMESTAMP}"
    print_info "=========================================="

    # Setup phase
    setup_directories
    check_dependencies
    setup_keypair
    configure_solana "${ENVIRONMENT}"
    check_balance "${ENVIRONMENT}"

    # Build phase
    build_program

    # Deploy/upgrade phase
    local program_id
    if [ "${UPGRADE_MODE}" = true ]; then
        upgrade_program
        program_id=$(get_program_id)
    else
        deploy_new
        program_id=$(get_program_id)
    fi

    # Verify phase
    verify_deployment "${program_id}"

    # Summary
    generate_summary "${program_id}" "${ENVIRONMENT}" \
        "$([ "${UPGRADE_MODE}" = true ] && echo "UPGRADE" || echo "NEW")"

    print_success "=========================================="
    print_success "Deployment completed successfully!"
    print_success "=========================================="
    print_info "Program ID: ${program_id}"
    print_info "Log: ${LOG_FILE}"
}

# Run main
main "$@"
