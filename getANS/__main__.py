from . import cli, __version__
import sys

if __name__ == "__main__":
    if sys.version_info[0] != 3 or sys.version_info[1]<8:

        raise RuntimeError("{} {} ".format("getiANS", __version__) +
                          "is not compatible with Python {0}.{1}.".format(
                                                        sys.version_info[0],
                                                        sys.version_info[1]) +
                          "\n\nPlease use Python 3.10 or higher.")

    cli.run()
