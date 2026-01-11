# main.py
# Application entry point with configuration management
# Implements document-centric workflow and application lifecycle
# Reference: https://doc.qt.io/qt-6/qtgui-index.html
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import argparse
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow
from utils.logging import setup_logging, get_logger
from utils.error_handling import ApplicationError, RecoveryPoint
from utils.configuration import load_configuration

logger = get_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='DXF Object Segregator')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    parser.add_argument('--benchmark', action='store_true',
                        help='Enable benchmarking mode')
    parser.add_argument('--no-gui', action='store_true',
                        help='Run in headless mode (for benchmarking)')
    parser.add_argument('--input', type=str, help='Input DXF file path')
    parser.add_argument('--output', type=str, help='Output project file path')
    return parser.parse_args()


def load_default_config() -> Dict[str, Any]:
    """Load default configuration"""
    return {
        'vertex_sharing_mode': 1,
        'intersection_mode': 1,
        'grouping_mode': 1,
        'tree_mode': 1,
        'tolerance_percent': 1.0,
        'benchmarking': {
            'enabled': False,
            'min_iterations': 5,
            'max_iterations': 100,
            'output_dir': 'benchmarks'
        },
        'logging': {
            'level': 'INFO',
            'file': 'dxf_segregator.log',
            'max_size': 10485760,  # 10MB
            'backup_count': 5
        },
        'ui': {
            'theme': 'system',
            'window_width': 1200,
            'window_height': 800,
            'recent_files': []
        }
    }


def run_headless_mode(args: argparse.Namespace, config: Dict[str, Any]):
    """
    Run application in headless mode for benchmarking or batch processing
    """
    from core.dxf_processor import DXFProcessor
    from utils.benchmarking import get_benchmark_suite

    logger.info("Running in headless mode")
    if not args.input:
        logger.error("Input DXF file required in headless mode")
        sys.exit(1)

    # Enable benchmarking if requested
    benchmark_suite = get_benchmark_suite()
    if args.benchmark or config.get('benchmarking', {}).get('enabled', False):
        benchmark_suite.enable()
        logger.info("Benchmarking enabled")

    # Process DXF file
    processor = DXFProcessor(config=config)
    try:
        with RecoveryPoint("headless_processing") as rp:
            object_tree = processor.process_dxf(args.input)
            if args.output:
                # Save results
                with open(args.output, 'w') as f:
                    json.dump(object_tree.to_dict(), f, indent=2)
                logger.info(f"Results saved to {args.output}")

            # Save benchmark results if enabled
            if benchmark_suite.enabled:
                results_file = benchmark_suite.save_results()
                csv_file = benchmark_suite.export_csv()
                report = benchmark_suite.generate_report()
                logger.info(f"Benchmark results saved to {results_file}")
                logger.info(f"Benchmark CSV exported to {csv_file}")
                logger.info(f"Benchmark report:\n{report}")
    except ApplicationError as e:
        logger.error(f"Processing failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


def run_gui_mode(args: argparse.Namespace, config: Dict[str, Any]):
    """
    Run application in GUI mode
    """
    app = QApplication(sys.argv)
    app.setApplicationName("DXF Object Segregator")
    app.setOrganizationName("YourOrganization")
    app.setOrganizationDomain("yourorganization.com")

    # Set application style
    theme = config.get('ui', {}).get('theme', 'system')
    if theme == 'dark':
        app.setStyle('Fusion')
        # Dark theme palette would be set here

    # Create main window
    main_window = MainWindow(config=config)

    # Load recent files if available
    recent_files = config.get('ui', {}).get('recent_files', [])
    if recent_files and os.path.exists(recent_files[0]):
        main_window.open_dxf_file(recent_files[0])

    # Show window
    main_window.show()

    # Start event loop
    exit_code = app.exec()

    # Save configuration on exit
    try:
        config['ui']['recent_files'] = main_window.get_recent_files()[:5]  # Save last 5 files
        config_file = Path.home() / '.dxf_segregator' / 'config.json'
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {config_file}")
    except Exception as e:
        logger.warning(f"Failed to save configuration: {str(e)}")

    sys.exit(exit_code)


def main():
    """Main entry point"""
    try:
        # Parse arguments
        args = parse_arguments()

        # Load configuration
        config = load_default_config()
        if args.config and os.path.exists(args.config):
            try:
                with open(args.config, 'r') as f:
                    user_config = json.load(f)
                config.update(user_config)
                logger.info(f"Loaded configuration from {args.config}")
            except Exception as e:
                logger.warning(f"Failed to load config file {args.config}: {str(e)}")

        # Set up logging
        log_level = args.log_level or config.get('logging', {}).get('level', 'INFO')
        log_file = config.get('logging', {}).get('file', 'dxf_segregator.log')
        setup_logging(level=log_level, log_file=log_file)
        logger.info("DXF Object Segregator started")
        logger.info(f"Configuration: {json.dumps(config, indent=2)}")

        # Set benchmarking mode if requested
        from utils.benchmarking import get_benchmark_suite
        benchmark_suite = get_benchmark_suite()
        if args.benchmark:
            benchmark_suite.enable()
            config['benchmarking']['enabled'] = True
            logger.info("Benchmarking mode enabled")

        # Choose mode based on arguments
        if args.no_gui:
            run_headless_mode(args, config)
        else:
            run_gui_mode(args, config)

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Application failed to start: {str(e)}", exc_info=True)
        print(f"Critical error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
