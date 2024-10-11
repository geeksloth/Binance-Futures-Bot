from recyclebin.binancesloth import BinanceSloth
import argparse

parser = argparse.ArgumentParser(description="BinanceSloth bot by GeekSloth")
parser.add_argument("-c", "--config", help="configuration JSON file", default="config.json")
args = vars(parser.parse_args())

bot = BinanceSloth(config=args["config"])
print(bot.logging.tint("Test colored msg", color="LIGHTGREEN_EX"))
print("end main")