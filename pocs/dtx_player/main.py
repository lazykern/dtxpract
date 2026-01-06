import sys
import logging
import traceback
from dtx import Dtx
from gameplay import Game


def main():
    """Main function to run the DTX player from the command line."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)-7s] %(message)s',
        datefmt='%H:%M:%S'
    )
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_dtx_file>")
        sys.exit(1)

    dtx_file_path = sys.argv[1]

    try:
        dtx_data = Dtx(dtx_file_path)
        dtx_data.parse()

        game = Game(dtx_data)
        game.run()

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

