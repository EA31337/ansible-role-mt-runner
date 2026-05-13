import io
from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError
import sys
import re
from bs4 import BeautifulSoup
import csv
import json
import argparse
import chardet
import xml.etree.ElementTree as ET

def parse_spread(value):
    # return e.g., "Current" and "30" from such pattern: "Current (30)". Current and 30 may change.
    # Regular expression pattern to extract values
    pattern = r'(\w+)\s*\((\d+)\)'
    match = re.match(pattern, value)
    if match:
        return {
            "type": match[1],
            "value": convert_value(match[2])
        }

    pattern = r'(\d+)'
    match = re.match(pattern, value)
    if match:
        return {
            "type": 'Unset',
            "value": convert_value(match[1])
        }

    raise AnsibleError("Could not parse spread value for parse_spread()! Passed: \"%s\"" % value)

def parse_symbol(value):
    # Return first letters from the value until space or end of line.
    return re.match(r'([A-Z]+)', value)[1]

def parse_period(value):
    # Regular expression pattern to extract values
    pattern = r'(\w+)\s*\((\d{4}\.\d{2}\.\d{2})\s*-\s*(\d{4}\.\d{2}\.\d{2})\)'

    if match := re.match(pattern, value):
        return {
            "period": match[1],
            "date_start": match[2],
            "date_end": match[3]
        }

    # If no match, try to to use this pattern: 1 Minute (M1) 2023.01.13 00:00 - 2023.01.23 23:59 (2023.01.13 - 2023.01.24)
    # For period it would be M1, for date_start it would be 2023.01.13, for date end it would be 2023.01.23.
    pattern = r'.*?\((\w+)\)\s+(\d{4}\.\d{2}\.\d{2}).*?\-\s+(\d{4}\.\d{2}\.\d{2})'

    if match := re.match(pattern, value):
        return {
            "period": match[1],
            "date_start": match[2],
            "date_end": match[3]
        }

    raise AnsibleError("Could not parse period for parse_period()! Passed: \"%s\"" % value)

def parse_val_prc(value):
    match = re.match(r'(-*\d+(\.\d+)*)\s+\((-*\d+(\.\d+)*)%\)', value)
    if match:
        return {
            "value": convert_value(match.group(1)),
            "percentage": convert_value(match.group(3))
        }
    else:
        raise AnsibleError("Could not parse value for parse_val_prc()! Passed: \"%s\"" % value)

def parse_prc_val(value):
    match = re.match(r'(-*\d+(\.\d+)*)%\s+\((-*\d+(\.\d+)*)\)', value)
    if match:
        return {
            "value": convert_value(match[3]),
            "percentage": convert_value(match[1])
        }
    raise AnsibleError("Could not parse value for parse_prc_val()! Passed: \"%s\"" % value)

def parse_val_of(value):
    match = re.match(r'(-*\d+(\.\d+)*)\s+\((-*\d+(\.\d+)*)\)', value)
    if match:
        return {
            "value": convert_value(match.group(1)),
            "of": convert_value(match.group(3))
        }
    else:
        raise AnsibleError("Could not parse value for parse_val_of()! Passed: \"%s\"" % value)

def parse_val_diff(value):
    if match := re.match(r'(-*\d+(\.\d+)*)\s+\((-*\d+(\.\d+)*)\)', value):
        return {"value": convert_value(match[1]), "diff": convert_value(match[3])}
    raise AnsibleError("Could not parse value for parse_val_diff()! Passed: \"%s\"" % value)

def parse_time(value):
    match = re.match(r'(\d+):(\d+):(\d+)', value)
    if match:
        return {
            "h": convert_value(match.group(1)),
            "m": convert_value(match.group(2)),
            "s": convert_value(match.group(3))
        }
    else:
        raise AnsibleError("Could not parse time for parse_time()! Passed: \"%s\"" % value)

def convert_value(value):
    if value.lower() == 'true':
        return True
    elif value.lower() == 'false':
        return False
    try:
        return int(value.replace(" ", "").replace("%", ""))
    except ValueError:
        try:
            return float(value.replace(" ", "").replace("%", ""))
        except ValueError:
            # Return the original string if conversion fails.
            return value

def extract_header_table(html_content):
    # Detecting whether it's MT4 report. We need to check if html_content string contains "Modelling Quality" text.
    is_mt4 = "Modelling quality" in html_content

    soup = BeautifulSoup(html_content, "html.parser")
    # Find the table with the specified div content.
    table = soup.find_all('table')[0]

    rows = []

    if is_mt4:
        # Extract expert advisor name from the table. It's the first sibling of the div above Strategy Tester Report.
        expert_name = soup.find('b', string="Strategy Tester Report").find_parent('div').find_next_sibling('div').text.strip()
        rows.append(["Expert:", expert_name])

    # Extract pairs of td values.
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        values = [col.text.strip() for col in tds]
        rows.append(values)

    data = {}

    # Extracting settings.

    now_inputs = False

    i = -1

    while True:
        i += 1 # Note we start from -1.

        if i >= len(rows):
            break

        # if i < 4:
        #     continue

        if len(rows[i]) == 0:
            continue

        key = rows[i][0]
        value = rows[i][1] if len(rows[i]) > 1 else ''

        # Remove trailing spaces and colons from the key.
        key = key.rstrip(':').strip().lower()

        # Expert
        if key == "expert":
            data["expert"] = convert_value(value)
        # Symbol
        elif key == "symbol":
            data["symbol"] = parse_symbol(value)
        # Period
        # Date Start
        # Date End
        elif key == "period":
            period = parse_period(value)
            data["period"] = period["period"]
            data["date_start"] = period["date_start"]
            data["date_end"] = period["date_end"]
        # Inputs
        elif key == "inputs":
            data["inputs"] = {}
            # Starting from the same row as "Inputs:".
            for input_i in range(i, len(rows)):
                if rows[input_i][1] == "=":
                    continue
                elif input_i > i and rows[input_i][0] != "":
                    # End of inputs.
                    break

                (input_key, input_value) = rows[input_i][1].split("=")
                data["inputs"][input_key] = convert_value(input_value)

            i = input_i
        # Inputs (MT4)
        elif key == "parameters":
            data["inputs"] = {}
            values = rows[i][1].split(";")
            for k in range(0, len(values)):
                if values[k] == "":
                    continue
                (input_key, input_value) = values[k].split("=")
                data["inputs"][input_key.strip()] = convert_value(input_value)
        # Currency ?
        elif key == "currency":
            data["currency"] = value
        # Initial Deposit
        # Spread (MT4 only)
        elif key == "initial deposit":
            data["initial_deposit"] = convert_value(value)
            if is_mt4:
                data["spread"] = parse_spread(rows[i][5])
        # Leverage ?
        elif key == "leverage":
            data["leverage"] = convert_value(value.split(":")[0]) / convert_value(value.split(":")[1])
        # History Quality ?
        elif key == "history quality":
            data["history_quality"] = convert_value(value.split("%")[0])
        # Bars
        # Ticks ?
        # Symbols ?
        # Modelling Quality (MT4)
        elif key == "bars":
            data["bars"] = convert_value(value)
            data["ticks"] = convert_value(rows[i][3])
            data["symbols"] = convert_value(rows[i][5])
        elif key == "bars in test": # MT4
            data["bars"] = convert_value(value)
            data["ticks"] = convert_value(rows[i][3])
            data["modelling_quality"] = convert_value(rows[i][5])
            # @todo
            data["symbols"] = 1
        # Mismached charts errors (MT4 only)
        elif key == "mismatched charts errors":
            data["mismatched_charts_errors"] = convert_value(value)
        # Total Net Profit
        # Balance Drawdown Absolute
        # Equity Drawdown Absolute
        elif key == "total net profit":
            data["total_net_profit"] = convert_value(value)
            if is_mt4:
                data["gross_profit"] = convert_value(rows[i][3])
                data["gross_loss"] = convert_value(rows[i][5])
            else:
                data["balance_drawdown_absolute"] = convert_value(rows[i][3])
                data["equity_drawdown_absolute"] = convert_value(rows[i][5])

        # Gross Profit (for MT4 is's a part of Total Net Profit)
        # Balance Drawdown Maximal (MT5 here)
        # Equity Drawdown Maximal (MT5 here)
        elif key == "gross profit":
            data["gross_profit"] = convert_value(value)
            data["balance_drawdown_maximal"] = parse_val_prc(rows[i][3])
            data["equity_drawdown_maximal"] = parse_val_prc(rows[i][5])
        # Balance Drawdown Absolute (MT4 here) ? Not sure if it's correct.
        # Balance Drawdown Maximal (MT4 here) ? Not sure if it's correct.
        # Balance Drawdown Relative (MT4 here) ? Not sure if it's correct.
        elif key == "absolute drawdown":
            data["balance_drawdown_absolute"] = convert_value(value)
            data["balance_drawdown_maximal"] = parse_val_prc(rows[i][3])
            data["balance_drawdown_relative"] = parse_prc_val(rows[i][5])
        # Gross Loss (for MT4 is's a part of Total Net Profit)
        # Balance Drawdown Relative ?
        # Equity Drawdown Relative ?
        elif key == "gross loss":
            data["gross_loss"] = convert_value(value)
            data["balance_drawdown_relative"] = parse_prc_val(rows[i][3])
            data["equity_drawdown_relative"] = parse_prc_val(rows[i][5])
        # Profit Factor
        # Expected Payoff
        # Margin Level
        elif key == "profit factor":
            data["profit_factor"] = convert_value(value)
            data["expected_payoff"] = convert_value(rows[i][3])
            data["margin_level"] = convert_value(rows[i][5])
        # Recovery Factor ?
        # Sharpe Ratio ?
        # Z-Score ?
        elif key == "recovery factor":
            data["recovery_factor"] = convert_value(value)
            data["sharpe_ratio"] = convert_value(rows[i][3])
            data["z_score"] = parse_val_prc(rows[i][5])
        # AHPR ?
        # LR Correlation ?
        # OnTester Result ?
        elif key == "ahpr":
            data["ahpr"] = parse_val_prc(value)
            data["lr_correlation"] = convert_value(rows[i][3])
            data["ontester_result"] = convert_value(rows[i][5])
        # GHPR ?
        # LR Standard Error ?
        elif key == "ghpr":
            data["ghpr"] = parse_val_prc(value)
            data["lr_standard_error"] = convert_value(rows[i][3])
        # Total Deals / Total Trades (MT5)
        # Profit Trades (MT5)
        # Loss Trades (MT5)
        elif key == "total deals":
            data["total_deals"] = convert_value(value)
            data["profit_trades"] = parse_val_prc(rows[i][3])
            data["loss_trades"] = parse_val_prc(rows[i][5])
        # Profit Trades (MT4)
        # Loss Trades (MT4)
        elif value == "Profit trades (% of total)":
            data["profit_trades"] = parse_val_prc(rows[i][2])
            data["loss_trades"] = parse_val_prc(rows[i][4])
        # Total Deals / Total Trades (MT4)
        # Short Trades / Short Positions (MT4)
        # Long Trades / Long Positions (MT4)
        elif key == "total trades":
            data["total_trades"] = convert_value(value)
            data["short_trades_won"] = parse_val_prc(rows[i][3])
            data["long_trades_won"] = parse_val_prc(rows[i][5])
        # Largest Profit trade
        # Largest Loss trade
        elif value == "largest profit trade" or (key == "largest" and value == "profit trade"):
            data["largest_profit_trade"] = convert_value(rows[i][2])
            data["largest_loss_trade"] = convert_value(rows[i][4])
        # Average Frofit Trade
        # Average Loss Trade
        elif value == "average profit trade" or (key == "average" and value == "profit trade"):
            data["average_profit_trade"] = convert_value(rows[i][2])
            data["average_loss_trade"] = convert_value(rows[i][4])
        # Maximum Consecutive Wins
        # Maximum Consecutive Losses
        elif value == "maximum" or (key == "maximum" and value == "consecutive wins (profit in money)"):
            data["maximum_consecutive_wins"] = parse_val_of(rows[i][2])
            data["maximum_consecutive_losses"] = parse_val_diff(rows[i][4])
        # Maximal Consecutive Wins
        # Maximal Consecutive Losses
        elif value == "maximal" or (key == "maximal" and value == "consecutive profit (count of wins)"):
            data["maximal_consecutive_profit"] = parse_val_of(rows[i][2])
            data["maximal_consecutive_losses_num"] = parse_val_diff(rows[i][4])
        # Average Consecutive Wins
        # Average Consecutive Losses
        elif value == "average" or (key == "average" and value == "consecutive wins"):
            data["average_consecutive_wins"] = convert_value(rows[i][2])
            data["average_consecutive_losses"] = convert_value(rows[i][4])
        # Correlation Profits MFE ?
        # Correlation Profits MAE ?
        # Correlation Profits MFE MAE ?
        elif key == "correlation (profits,mfe)":
            data["correlation_profits_mfe"] = convert_value(value)
            data["correlation_profits_mae"] = convert_value(rows[i][3])
            data["correlation_profits_mfe_mae"] = convert_value(rows[i][5])
        # Minimal Position Holding Time ?
        # Maximal Position Holding Time ?
        # Average Position Holding Time ?
        elif key == "minimal position holding time":
            data["minimal_position_holding_time"] = parse_time(value)
            data["maximal_position_holding_time"] = parse_time(rows[i][3])
            data["average_position_holding_time"] = parse_time(rows[i][5])
        else:
            pass # Skip row.

    return data


def extract_orders_table(html_content):
    re_orders = re.findall(pattern='Orders<.*?Comment</b>.*?</td>.*?</tr>(.*?)<tr>', string=html_content, flags=re.S)
    if not re_orders or len(re_orders[0]) == 0:
        # If no orders found, return empty list.
        return []

    html_content = "<div>" + re_orders[0] + "</div>"
    soup = BeautifulSoup(html_content, "html.parser")
    rows = soup.find_all("tr", {"bgcolor": ["#FFFFFF", "#F7F7F7"]})
    data = []

    for row in rows:
        columns = [td.get_text(strip=True) for td in row.find_all("td")]

        if not columns:
            break

        # Stop/Loss, Take/Profil columns.
        volume = columns[4].split(" / ");
        stop_loss = volume[0] if len(volume) > 0 else ""
        take_profit = volume[0] if len(volume) > 0 else ""

        data.append([columns[0], columns[1], columns[2], columns[3], stop_loss, take_profit, columns[5], columns[6], columns[7], columns[8], columns[9], columns[10]])

    return data

def extract_deals_table_mt4(html_content, unified=False):
    if unified:
        column_titles = ["Time", "Deal", "Symbol", "Type", "Direction", "Volume", "Price", "Order", "Commission", "Swap", "Profit", "Balance", "Comment"]
    else:
        column_titles = ["Deal", "Time", "Type", "Order", "Size", "Price", "S / L", "T / P", "Profit", "Balance"]

    re_deals = re.findall(pattern='<td>Balance</td>.*?</tr>\s*(.*?)\s*</table>', string=html_content, flags=re.S)

    if not re_deals or len(re_deals[0]) == 0:
        # If no deals found, return empty list.
        return (column_titles, [])

    html_content = "<div>" + re_deals[0] + "</div>"
    soup = BeautifulSoup(html_content, "html.parser")
    rows = soup.findChildren("tr")

    data = []

    for row in rows:
        columns = [td.get_text(strip=True) for td in row.find_all("td")]
        # Expand columns table up to 10 columns.
        if len(columns) < 10:
            columns += [""] * (10 - len(columns))

        if unified:
            symbol = ""
            direction = ""
            volume = ""
            commission = ""
            swap = ""
            comment = ""

            # ........................0..., 1..., 2.......3...., 4........, 5....., 6...., 7...., 8........., 9..., 10...., 11....., 12
            # The order we expect is: Time, Deal, Symbol, Type,  Direction, Volume, Price, Order, Commission, Swap, Profit, Balance, Comment.
            # The order we get is:    Deal, Time, Type,   Order, Size,      Price,  S / L, T / P, Profit,     Balance.
            data.append([columns[1], columns[0], symbol, columns[2], direction, volume, columns[5], columns[3], commission, swap, columns[8], columns[9], comment])
        else:
            data.append(columns)

    return (column_titles, data)

def extract_deals_table_mt5(html_content):
    column_titles = ["Time", "Deal", "Symbol", "Type", "Direction", "Volume", "Price", "Order", "Commission", "Swap", "Profit", "Balance", "Comment"]

    re_deals = re.findall(pattern='Deals<.*?Comment</b>.*?</td>.*?</tr>(.*?)<tr>', string=html_content, flags=re.S)

    if not re_deals or len(re_deals[0]) == 0:
        # If no deals found, return empty list.
        return (columns, [])

    html_content = "<div>" + re_deals[0] + "</div>"
    soup = BeautifulSoup(html_content, "html.parser")
    rows = soup.find_all("tr", {"bgcolor": ["#FFFFFF", "#F7F7F7"]})

    data = []

    for row in rows:
        columns = [td.get_text(strip=True) for td in row.find_all("td")]
        data.append(columns)

    return (column_titles, data)

def write_to_csv(data, output_file, include_titles=True, type=None, return_string=False):
    # Detecting whether it's MT4 report. We need to check if html_content string contains "Modelling Quality" text.
    is_mt4 = "Modelling quality" in data

    # Write data to CSV
    if return_string:
        csvfile = io.StringIO(newline="\n")
    else:
        csvfile = open(output_file, "w", newline="", encoding="utf-8")

    writer = csv.writer(csvfile, )

    if is_mt4 and type == "orders":
        # Orders are only available in MT5. We change the type implicitly to deals for MT4.
        type = "deals"

    if type == "orders":
        columns = ["Open Time", "Order", "Symbol", "Type", "Volume 1", "Volume 2", "Price", "Stop / Loss", "Take / Profit", "Time", "State", "Comment"]
        rows = extract_orders_table(data)
    elif type == "deals":
        if is_mt4:
            (columns, rows) = extract_deals_table_mt4(data, unified=False)
        else:
            (columns, rows) = extract_deals_table_mt5(data)
    elif type == "opt":
        (columns, rows) = data
    else:
        raise AnsibleError("Invalid --type passed!")

    if include_titles:
        writer.writerow(columns)  # Write header

    for row in rows:
        writer.writerow(row)

    if return_string:
        return csvfile.getvalue()
    else:
        csvfile.close()

def write_to_json(html_content, output_file, type, return_string=False):
    if return_string:
        jsonfile = io.StringIO()
    else:
        jsonfile = open(output_file, "w", newline="\n", encoding="utf-8")

    if type == "header":
        obj = extract_header_table(html_content)
    else:
        raise AnsibleError("Invalid --type passed!")

    jsonfile.write(json.dumps(obj, indent=4))

    if return_string:
        return jsonfile.getvalue()
    else:
        jsonfile.close()

def write_opt(content, output_file, include_titles, return_string=False):
    # Detecting whether it's MT5 report. We need to check if html_content string contains "<?xml" text.
    is_mt5 = "<?xml" in content

    if is_mt5:
        return write_opt_mt5(content, output_file, include_titles, return_string=return_string)
    else:
        return write_opt_mt4(content, output_file, include_titles, return_string=return_string)

def write_opt_mt5(content, output_file, include_titles, return_string=False):
    tree = ET.ElementTree(ET.fromstring(content))
    root = tree.getroot()

    # Define namespaces.
    ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}

    # Find the Table element.
    table = root.find('.//ss:Table', ns)

    if table is None:
        return write_to_csv([["Pass", "Result", "Profit", "Expected Payoff", "Profit Factor", "Recovery Factor", "Sharpe Ratio", "Custom", "Equity DD %"], []], output_file, include_titles, "opt", return_string=return_string)
    else:
        # Extract column names
        columns = [cell.find('./ss:Data', ns).text for cell in table.find('./ss:Row', ns)]

        data = []
        for row in sorted(table.findall('./ss:Row', ns)[1:], key=lambda x: float(x.find('./ss:Cell/ss:Data', ns).text)):
            row_data = [cell.find('./ss:Data', ns).text for cell in row]
            data.append(row_data)

        return write_to_csv([columns, data], output_file, include_titles, "opt", return_string=return_string)

def write_opt_mt4(html_content, output_file, include_titles, return_string=False):
    column_titles = ["Pass", "Profit", "Total Trades", "Profit Factor", "Expected Payoff", "Drawdown $", "Drawdown %"]

    soup = BeautifulSoup(html_content, "html.parser")
    data = []

    table = soup.find_all("table")[1]

    if table:
        rows = table.find_all("tr")
        data = []

        for row in rows[1:]:
            columns = [td.get_text(strip=True) for td in row.find_all("td")]
            data.append(columns)

    return write_to_csv([column_titles, data], output_file, include_titles, "opt", return_string=return_string)

def main(input_file_path, output_file_path, include_titles = False, type = None, return_string=False):
    if type == None:
        raise AnsibleError("Type (--type parameter) is not set!")

    if type in ["orders", "deals", "header", "opt"]:
        try:
            # Report file could be in UTF-16LE or UTF-8 encoding.
            with open(input_file_path, "rb") as f:
                raw_data = f.read()
                detected_encoding = chardet.detect(raw_data)['encoding']
            try:
                html_content = raw_data.decode(detected_encoding)
            except Exception as e:
                raise AnsibleError(f"Failed to decode file with detected encoding '{detected_encoding}': {str(e)}")
            # Fixes wrong HTML tag in the report for MetaTrader 4.
            html_content = html_content.replace("<tr align=left><td>Bars in test", "Bars in test")

            if type in ["orders", "deals", "header"] and "Strategy Tester Report" not in html_content:
                raise AnsibleError("Wrong file passed. It's not an MT report file!")
            elif type in ["opt"] and ("Optimization Report" not in html_content and "Tester Optimizator Results" not in html_content):
                raise AnsibleError("Wrong file passed. It's not an MT optimization report file!")

        except FileNotFoundError:
            raise AnsibleError("File not found: " + input_file_path)
        except Exception as e:
            raise AnsibleError("An error occurred: " + str(e))

    if type in ["orders", "deals"]:
        return write_to_csv(html_content, output_file_path, include_titles, type, return_string=return_string)
    elif type in ["header"]:
        return write_to_json(html_content, output_file_path, type, return_string=return_string)
    elif type in ["opt"]:
        return write_opt(html_content, output_file_path, include_titles, return_string=return_string)

    raise ValueError('Incorrect type passed. Allowed value: "orders" OR "deals" OR "header" OR "opt".')

class LookupModule(LookupBase):
    # Expecting the same list of arguments as the "main" function.
    def run(self, terms, variables=None, **kwargs):
        if len(terms) != 3:
            raise AnsibleError('parse_mt_report requires exactly 3 parameters to be passed:\n1) input file path\n2) type of file: "orders"|"deals"|"header"|"opt"\n3) include titles?')
        (input_file_path, type, include_titles) = terms
        return [main(input_file_path, '', include_titles, type, True)]

if __name__ == "__main__":
        parser = argparse.ArgumentParser(description="Parse MT report and extract data.")
        parser.add_argument("input_file_path", help="Path to the input file.")
        parser.add_argument("--out", help="Path to the output file. When not passed, string will be returned.")
        parser.add_argument("--type", choices=["orders", "deals", "header", "opt"], required=True, help="Type of data to extract.")
        parser.add_argument("--titles", action="store_true", help="Include titles in the output.")

        args = parser.parse_args()

        try:
            result = main(
                input_file_path=args.input_file_path,
                output_file_path=args.out,
                include_titles=args.titles,
                type=args.type,
                return_string=not args.out
            )
            if not args.out:
                print(result)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

# Testing:
# lm = LookupModule()
# print(lm.run(sys.argv[1:]))
