import sys

from . import wikitablestosql


def main(args=None):
    """The main routine."""
    if args is None:
        wikitablestosql.main()


if __name__ == "__main__":
    sys.exit(main())
