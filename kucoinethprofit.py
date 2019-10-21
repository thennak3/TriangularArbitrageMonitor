import ccxt.async
from threading import *
import threading
import logging

screen_lock = Semaphore(value=1)


def main_loop():
    kucoin = ccxt.kucoin()
    threads = {}
    counter = 0
    while True:
        try:
            kcmarkets = kucoin.load_markets(True)

            pairings = []

            ethbuy = 0.0
            ethsell = 0.0

            valset = False

            for key, value in kcmarkets.items():
                base = value['base']
                quote = value['quote']
                if base == 'ETH' or quote == 'ETH':
                    if base != 'ETH':
                        tocheck = base
                    else:
                        tocheck = quote

                    if not tocheck in pairings and tocheck != 'BTC':
                        pairings.append(tocheck)
                if not valset and base == 'BTC' and quote == 'ETH':
                    ethbuy = value['info']['buy']
                    ethsell = value['info']['sell']
                    valset = True
                elif not valset and base == 'ETH' and quote == 'BTC':
                    ethbuy = value['info']['buy']
                    ethsell = value['info']['sell']
                    valset = True

            btc = {}
            eth = {}

            for key, value in kcmarkets.items():
                base = value['base']
                quote = value['quote']
                proceed = False
                isbase = False
                if base == 'BTC' or base == 'ETH':
                    proceed = True
                    isbase = True
                elif quote == 'BTC' or quote == 'ETH':
                    proceed = True
                    isbase = False
                if base == 'ETH' and quote == 'BTC' or base == 'BTC' and quote == 'ETH':
                    continue
                if proceed and quote in pairings or base in pairings:
                    if isbase:
                        if base == 'BTC':
                            btc[quote] = {}
                            btc[quote]['symbol'] = value['symbol']
                            btc[quote]['buy'] = value['info']['buy']
                            btc[quote]['sell'] = value['info']['sell']
                        elif base == 'ETH':
                            eth[quote] = {}
                            eth[quote]['symbol'] = value['symbol']
                            eth[quote]['buy'] = value['info']['buy']
                            eth[quote]['sell'] = value['info']['sell']
                    else:
                        if quote == 'BTC':
                            btc[base] = {}
                            btc[base]['symbol'] = value['symbol']
                            btc[base]['buy'] = value['info']['buy']
                            btc[base]['sell'] = value['info']['sell']
                        elif quote == 'ETH':
                            eth[base] = {}
                            eth[base]['symbol'] = value['symbol']
                            eth[base]['buy'] = value['info']['buy']
                            eth[base]['sell'] = value['info']['sell']

            totaleth = 5
            totalbtc = totaleth * ethsell

            stroutput = ""
            #stroutput += 'Total BTC {:8f}'.format(totalbtc)
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
                    ethpair = eth[pair]['buy']

                    if pair == 'USDT':
                        secondval = firstval / ethpair
                    else:
                        secondval = firstval * ethpair

                    secondval *= 0.999
                    thirdval = secondval * ethbuy
                    thirdval *= 0.999
                    if thirdval > totalbtc:
                        s1 = "\nProfitable Pair BTC/{} Difference {:.8f} Percentage {:.2f}".format(pair, thirdval - totalbtc, (1-(totalbtc / thirdval)) * 100)
                        stroutput += s1
                        if not pair + '/BTC' in threads:
                            t1 = threading.Thread(target=currencymonitor, args=[pair, 'BTC', 1-(totalbtc / thirdval)])
                            threads[pair + '/BTC'] = t1
                            t1.start()

                    firstval = totalbtc / ethsell
                    firstval *= 0.999

                    ethval = eth[pair]['sell']
                    if pair == 'USDT':
                        secondval = firstval * ethval
                    else:
                        secondval = firstval / ethval
                    secondval *= 0.999

                    btcval = btc[pair]['buy']
                    if pair == 'USDT':
                        thirdval = secondval / btcval
                    else:
                        thirdval = secondval * btcval

                    if thirdval > totalbtc:
                        s1 = "\nProfitable Pair ETH/{} Difference {:.8f} Percentage {:.2f}".format(pair, thirdval - totalbtc, (1-(totalbtc / thirdval)) * 100)
                        stroutput += s1
                        if not pair + '/ETH' in threads:
                            t1 = threading.Thread(target=currencymonitor, args=[pair, 'ETH', 1 - (totalbtc / thirdval)])
                            threads[pair + '/ETH'] = t1
                            t1.start()


                except KeyError:
                    if pair != "CFD":
                        screen_lock.acquire()
                        #print(pair, " doesn't exist")
                        screen_lock.release()
            #screen_lock.acquire()
            #print(stroutput)
            #screen_lock.release()
            counter += 1
            if counter > 500:
                screen_lock.acquire()
                print('Still alive..')
                screen_lock.release()
                counter = 0
            for k, v in list(threads.items()):
                if not v.isAlive():
                    del threads[k]

        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            screen_lock.acquire()
            #print(message)
            screen_lock.release()


def currencymonitor(pair, direction, profper):
    kucoinage = ccxt.kucoin()
    profitable = True
    deathcounter = 5
    if pair != 'USDT':
        while profitable:
            try:
                pairbtc = kucoinage.fetch_order_book(pair + "/BTC", 1)
                paireth = kucoinage.fetch_order_book(pair + "/ETH", 1)
                ethbtc = kucoinage.fetch_order_book("ETH/BTC", 1)
                if direction == 'BTC':
                    if pair != 'USDT':
                        try:
                            volavail = ethbtc['bids'][0][1] / paireth['bids'][0][0]
                            if volavail > paireth['bids'][0][1]:
                                volavail = paireth['bids'][0][1]
                            if volavail > pairbtc['asks'][0][1]:
                                volavail = pairbtc['asks'][0][1]
                            startbtc = volavail * pairbtc['asks'][0][0]
                            startbtc *= 1.001
                            #calculate profitability
                            firstval = startbtc / pairbtc['asks'][0][0]
                            firstval *= 0.999
                            secondval = firstval * paireth['bids'][0][0]
                            secondval *= 0.999
                            thirdval = secondval * ethbtc['bids'][0][0]
                            thirdval *= 0.999
                            #screen_lock.acquire()
                            #prstring = "Pair {}/BTC Start {:.8f} End {:8f} Profit {:.8f}".format(pair, startbtc, thirdval,
                            #                                                                     thirdval - startbtc)
                            #print(prstring)
                            #screen_lock.release()
                            if thirdval > startbtc and thirdval - startbtc > 0.0001:
                                screen_lock.acquire()
                                prstring = "Pair {}/BTC Start {:.8f} End {:8f} Profit {:.8f}".format(pair, startbtc, thirdval, thirdval - startbtc)
                                print(prstring)
                                screen_lock.release()
                                deathcounter = 5
                            else:
                                deathcounter -= 1
                                if deathcounter == 0:
                                    profitable = False
                        except IndexError:
                            screen_lock.acquire()
                            print('Issue with ' + pair + '/BTC Stuff')
                            profitable = False
                            screen_lock.release()
                        #todo:figure out how to tell potential profit by examining trades on both sides, should be rather simple as it's the same calculation as above..
                    else:
                        break
                else:
                    if pair != 'USDT':
                        try:
                            volavail = pairbtc['bids'][0][1]
                            if volavail > paireth['asks'][0][1]:
                                volavail = paireth['asks'][0][1]
                            volavail = volavail * paireth['asks'][0][0]
                            if ethbtc['asks'][0][0] < volavail:
                                volavail = ethbtc['asks'][0][1]
                            startbtc = volavail * ethbtc['asks'][0][0]
                            startbtc *= 1.001
                            # calculate profitability
                            firstval = startbtc / ethbtc['asks'][0][0]
                            firstval *= 0.999
                            secondval = firstval / paireth['asks'][0][0]
                            secondval *= 0.999
                            thirdval = secondval * pairbtc['bids'][0][0]
                            thirdval *= 0.999
                            if thirdval > startbtc and thirdval - startbtc > 0.0001:
                                screen_lock.acquire()
                                prstring = "Pair {}/ETH Start {:.8f} End {:8f} Profit {:.8f}".format(pair, startbtc, thirdval, thirdval - startbtc)
                                print(prstring)
                                screen_lock.release()
                                deathcounter = 5
                            else:
                                deathcounter -= 1
                                if deathcounter == 0:
                                    profitable = False
                        except IndexError:
                            screen_lock.acquire()
                            #print('Issue with ' + pair + '/ETH Stuff')
                            profitable = False
                            screen_lock.release()
                    else:
                        break
            except Exception as ex:
                profitable = False
                print('Yeah if you could fix that thatd be great')

main_loop()
