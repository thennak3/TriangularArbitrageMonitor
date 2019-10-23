import ccxt.async_support


def main_loop():
    kucoin = ccxt.kucoin()
    while True:

        kcmarkets = kucoin.load_markets(True)

        pairings = []

        kcsbuy = 0.0
        kcssell = 0.0

        valset = False

        for key, value in kcmarkets.items():
            base = value['base']
            quote = value['quote']
            if base == 'KCS' or quote == 'KCS':
                if base != 'KCS':
                    tocheck = base
                else:
                    tocheck = quote

                if not tocheck in pairings and tocheck != 'BTC':
                    pairings.append(tocheck)
            if not valset and base == 'BTC' and quote == 'KCS':
                kcsbuy = value['info']['buy']
                kcssell = value['info']['sell']
                valset = True
            elif not valset and base == 'KCS' and quote == 'BTC':
                kcsbuy = value['info']['buy']
                kcssell = value['info']['sell']
                valset = True

        btc = {}
        kcs = {}

        for key, value in kcmarkets.items():
            base = value['base']
            quote = value['quote']
            proceed = False
            isbase = False

            if base == 'BTC' or base == 'KCS':
                proceed = True
                isbase = True
            elif quote == 'BTC' or quote == 'KCS':
                proceed = True
                isbase = False
            if base == 'KCS' and quote == 'BTC' or base == 'BTC' and quote == 'KCS':
                continue

            if proceed and quote in pairings or base in pairings:
                if isbase:
                    if base == 'BTC':
                        btc[quote] = {}
                        btc[quote]['symbol'] = value['symbol']
                        btc[quote]['buy'] = value['info']['buy'];
                        btc[quote]['sell'] = value['info']['sell'];
                    elif base == 'KCS':
                        kcs[quote] = {}
                        kcs[quote]['symbol'] = value['symbol']
                        kcs[quote]['buy'] = value['info']['buy'];
                        kcs[quote]['sell'] = value['info']['sell'];
                else:
                    if quote == 'BTC':
                        btc[base] = {}
                        btc[base]['symbol'] = value['symbol']
                        btc[base]['buy'] = value['info']['buy'];
                        btc[base]['sell'] = value['info']['sell'];
                    elif quote == 'KCS':
                        kcs[base] = {}
                        kcs[base]['symbol'] = value['symbol']
                        kcs[base]['buy'] = value['info']['buy'];
                        kcs[base]['sell'] = value['info']['sell'];

        totalkcs = 5
        totalbtc = totalkcs * kcssell

        print('Total BTC ', totalbtc)
        for pair in pairings:
            try:
                btcpair = btc[pair]['sell']
                firstval = 0
                if pair == 'USDT':
                    firstval = totalbtc * btcpair
                else:
                    firstval = totalbtc / btcpair

                firstval *= 0.999
                secondval = 0
                kcspair = kcs[pair]['buy']

                if pair == 'ETH' or pair == 'USDT':
                    secondval = firstval / kcspair
                else:
                    secondval = firstval * kcspair

                secondval *= 0.999
                thirdval = secondval * kcsbuy
                thirdval *= 0.999
                if thirdval > totalbtc:
                    s1 = "Profitable Pair BTC/{} Difference {:.8f} Percentage {:.2f}".format(pair, thirdval - totalbtc, (1-(totalbtc / thirdval)) * 100)
                    print(s1)

                firstval = totalbtc / kcssell
                firstval *= 0.999

                kcsval = kcs[pair]['sell']
                if pair == 'ETH' or pair == 'USDT':
                    secondval = firstval * kcsval
                else:
                    secondval = firstval / kcsval
                secondval *= 0.999

                btcval = btc[pair]['buy']
                if pair == 'USDT':
                    thirdval = secondval / btcval
                else:
                    thirdval = secondval * btcval

                if thirdval > totalbtc:
                    if pair == 'BCH':
                        print('BCH KCS ', kcsval, ' BTC ', btcval)
                    s1 = "Profitable Pair KCS/{} Difference {:.8f} Percentage {:.2f}".format(pair, thirdval - totalbtc, (1-(totalbtc / thirdval)) * 100)
                    print(s1)

            except KeyError:
                print(pair, " doesn't exist")


main_loop()
