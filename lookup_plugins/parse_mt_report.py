import io
from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError
import sys
import re
from bs4 import BeautifulSoup
import csv
import json
import xml.etree.ElementTree as ET

def parse_period(value):
    # Regular expression pattern to extract values
    pattern = r'(\w+)\s*\((\d{4}\.\d{2}\.\d{2})\s*-\s*(\d{4}\.\d{2}\.\d{2})\)'

    # Using regex to match the pattern.
    match = re.match(pattern, value)

    # Extracting values.
    if match:
        return {
            "period": match.group(1),
            "date_start": match.group(2),
            "date_end": match.group(3)
        }
    else:
        print("Could not parse date for parse_period()! Passed: \"%s\"" % value, file=sys.stderr)
        exit(1)

def parse_val_prc(value):
    match = re.match(r'(-*\d+(\.\d+)*)\s+\((-*\d+(\.\d+)*)%\)', value)
    if match:
        return {
            "value": convert_value(match.group(1)),
            "percentage": convert_value(match.group(3))
        }
    else:
        print("Could not parse value for parse_val_prc()! Passed: \"%s\"" % value, file=sys.stderr)
        exit(1)

def parse_prc_val(value):
    match = re.match(r'(-*\d+(\.\d+)*)%\s+\((-*\d+(\.\d+)*)\)', value)
    if match:
        return {
            "value": convert_value(match.group(3)),
            "percentage": convert_value(match.group(1))
        }
    else:
        print("Could not parse value for parse_prc_val()! Passed: \"%s\"" % value, file=sys.stderr)
        exit(1)

def parse_val_of(value):
    match = re.match(r'(-*\d+(\.\d+)*)\s+\((-*\d+(\.\d+)*)\)', value)
    if match:
        return {
            "value": convert_value(match.group(1)),
            "of": convert_value(match.group(3))
        }
    else:
        print("Could not parse value for parse_val_of()! Passed: \"%s\"" % value, file=sys.stderr)
        exit(1)

def parse_val_diff(value):
    match = re.match(r'(-*\d+(\.\d+)*)\s+\((-*\d+(\.\d+)*)\)', value)
    if match:
        return {
            "value": convert_value(match.group(1)),
            "diff": convert_value(match.group(3))
        }
    else:
        print("Could not parse value for parse_val_diff()! Passed: \"%s\"" % value, file=sys.stderr)
        exit(1)

def parse_time(value):
    match = re.match(r'(\d+):(\d+):(\d+)', value)
    if match:
        return {
            "h": convert_value(match.group(1)),
            "m": convert_value(match.group(2)),
            "s": convert_value(match.group(3))
        }
    else:
        print("Could not parse value for parse_time()! Passed: \"%s\"" % value, file=sys.stderr)
        exit(1)

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
    soup = BeautifulSoup(html_content, "html.parser")
    # Find the table with the specified div content.
    table = soup.find('b', string="Strategy Tester Report").find_parent('table')

    # Extract pairs of td values.
    rows = []
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        values = []
        for td in tds:
            values.append(td.text.strip())
        rows.append(values)

    data = {}
    
    # Extracting settings.

    now_inputs = False

    i = -1

    while True:
        i += 1 # Note we start from -1.

        if i >= len(rows):
            break

        if i < 4:
            continue

        if len(rows[i]) == 0:
            continue

        key = rows[i][0]
        value = rows[i][1] if len(rows[i]) > 1 else ''

        if key == "Expert:":
            data["expert"] = convert_value(value)
        elif key == "Symbol:":
            data["symbol"] = convert_value(value)
        elif key == "Period:":
            period = parse_period(value)
            data["period"] = period["period"]
            data["date_start"] = period["date_start"]
            data["date_end"] = period["date_end"]
        elif key == "Inputs:":
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
        elif key == "Currency:":
            data["currency"] = value
        elif key == "Initial Deposit:":
            data["initial_deposit"] = convert_value(value)
        elif key == "Leverage:":
            data["leverage"] = convert_value(value.split(":")[0]) / convert_value(value.split(":")[1])
        elif key == "History Quality:":
            data["history_quality"] = convert_value(value.split("%")[0])
        elif key == "Bars:":
            data["bars"] = convert_value(value)
            data["ticks"] = convert_value(rows[i][3])
            data["symbols"] = convert_value(rows[i][5])
        elif key == "Total Net Profit:":
            data["total_net_profit"] = convert_value(value)
            data["balance_drawdown_absolute"] = convert_value(rows[i][3])
            data["equity_drawdown_absolute"] = convert_value(rows[i][5])
        elif key == "Gross Profit:":
            data["gross_profit"] = convert_value(value)
            data["balance_drawdown_maximal"] = parse_val_prc(rows[i][3])
            data["equity_drawdown_maximal"] = parse_val_prc(rows[i][5])
        elif key == "Gross Loss:":
            data["gross_loss"] = convert_value(value)
            data["balance_drawdown_relative"] = parse_prc_val(rows[i][3])
            data["equity_drawdown_relative"] = parse_prc_val(rows[i][5])
        elif key == "Profit Factor:":
            data["profit_factor"] = convert_value(value)
            data["expected_payoff"] = convert_value(rows[i][3])
            data["margin_level"] = convert_value(rows[i][5])
        elif key == "Recovery Factor:":
            data["recovery_factor"] = convert_value(value)
            data["sharpe_ratio"] = convert_value(rows[i][3])
            data["z_score"] = parse_val_prc(rows[i][5])
        elif key == "AHPR:":
            data["ahpr"] = parse_val_prc(value)
            data["lr_correlation"] = convert_value(rows[i][3])
            data["ontester_result"] = convert_value(rows[i][5])
        elif key == "GHPR:":
            data["ghpr"] = parse_val_prc(value)
            data["lr_standard_error"] = convert_value(rows[i][3])
        elif key == "Total Trades:":
            data["total_trades"] = convert_value(value)
            data["short_trades_won"] = parse_val_prc(rows[i][3])
            data["long_trades_won"] = parse_val_prc(rows[i][5])
        elif key == "Total Deals:":
            data["total_deals"] = convert_value(value)
            data["profit_trades"] = parse_val_prc(rows[i][3])
            data["loss_trades"] = parse_val_prc(rows[i][5])
        elif value == "Largest profit trade:":
            data["largest_profit_trade"] = convert_value(rows[i][2])
            data["largest_loss_trade"] = convert_value(rows[i][4])
        elif value == "Average profit trade:":
            data["average_profit_trade"] = convert_value(rows[i][2])
            data["average_loss_trade"] = convert_value(rows[i][4])
        elif value == "Maximum :":
            data["maximum"] = parse_val_of(rows[i][2])
            data["maximum_consecutive_losses"] = parse_val_diff(rows[i][4])
        elif value == "Maximal :":
            data["maximal"] = parse_val_of(rows[i][2])
            data["maximal_consecutive_losses_num"] = parse_val_diff(rows[i][4])
        elif value == "Average :":
            data["average"] = convert_value(rows[i][2])
            data["average_consecutive_losses"] = convert_value(rows[i][4])
        elif key == "Correlation (Profits,MFE):":
            data["correlation_profits_mfe"] = convert_value(value)
            data["correlation_profits_mae"] = convert_value(rows[i][3])
            data["correlation_profits_mfe_mae"] = convert_value(rows[i][5])
        elif key == "Minimal position holding time:":
            data["minimal_position_holding_time"] = parse_time(value)
            data["maximal_position_holding_time"] = parse_time(rows[i][3])
            data["average_position_holding_time"] = parse_time(rows[i][5])
        else:
            pass # Skip row.
    return data


def extract_orders_table(html_content):
    html_content = "<div>" + re.findall(pattern='Orders<.*?Comment</b>.*?</td>.*?</tr>(.*?)<tr>', string=html_content, flags=re.S)[0] + "</div>"
    soup = BeautifulSoup(html_content, "html.parser")
    rows = soup.find_all("tr", {"bgcolor": ["#FFFFFF", "#F7F7F7"]})
    data = []

    for row in rows:
        columns = [td.get_text(strip=True) for td in row.find_all("td")]

        if len(columns) == 0:
            break

        # Stop/Loss, Take/Profil columns.
        volume = columns[4].split(" / ");
        stop_loss = volume[0] if len(volume) > 0 else ""
        take_profit = volume[0] if len(volume) > 0 else ""

        data.append([columns[0], columns[1], columns[2], columns[3], stop_loss, take_profit, columns[5], columns[6], columns[7], columns[8], columns[9], columns[10]])

    return data

def extract_deals_table(html_content):
    html_content = "<div>" + re.findall(pattern='Deals<.*?Comment</b>.*?</td>.*?</tr>(.*?)<tr>', string=html_content, flags=re.S)[0] + "</div>"
    soup = BeautifulSoup(html_content, "html.parser")
    rows = soup.find_all("tr", {"bgcolor": ["#FFFFFF", "#F7F7F7"]})

    data = []

    for row in rows:
        columns = [td.get_text(strip=True) for td in row.find_all("td")]
        data.append(columns)

    return data

def write_to_csv(data, output_file, include_titles=True, type=None, return_string=False):
    # Write data to CSV
    if return_string:
        csvfile = io.StringIO()
    else:
        csvfile = open(output_file, "w", newline="", encoding="utf-8")    
    
    writer = csv.writer(csvfile)

    # Define columns.
    if type == "orders":
        columns = ["Open Time", "Order", "Symbol", "Type", "Volume 1", "Volume 2", "Price", "Stop / Loss", "Take / Profit", "Time", "State", "Comment"]
        rows = extract_orders_table(data)
    elif type == "deals":
        columns = ["Time", "Deal", "Symbol", "Type", "Direction", "Volume", "Price", "Order", "Commission", "Swap", "Profit", "Balance", "Comment"]
        rows = extract_deals_table(data)
    elif type == "opt":
        (columns, rows) = data
    else:
        print("Invalid --type passed!", file=sys.stderr)
        exit(1)

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
        print("Invalid --type passed!", file=sys.stderr)
        exit(1)

    jsonfile.write(json.dumps(obj, indent=4))

    if return_string:
        return jsonfile.getvalue()
    else:
        jsonfile.close()

def write_opt(input_file, output_file, include_titles, return_string=False):
    tree = ET.parse(input_file)
    root = tree.getroot()

    # Define namespaces.
    ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}

    # Find the Table element.
    table = root.find('.//ss:Table', ns)

    # Extract column names
    columns = [cell.find('./ss:Data', ns).text for cell in table.find('./ss:Row', ns)]

    data = []
    for row in sorted(table.findall('./ss:Row', ns)[1:], key=lambda x: float(x.find('./ss:Cell/ss:Data', ns).text)):
        row_data = [cell.find('./ss:Data', ns).text for cell in row]
        data.append(row_data)

    return write_to_csv([columns, data], output_file, include_titles, "opt", return_string=return_string)

def main(input_file_path, output_file_path, include_titles = False, type = None, return_string=False):
    if type == None:
        print("--type parameter must be set!", file=sys.stderr)
        exit(1)
    if type in ["orders", "deals", "header"]:
        try:
            with open(input_file_path, "rb") as f:
                html_content = f.read().decode("utf-16le")
        except FileNotFoundError:
            raise AnsibleError("File not found: " + input_file_path)
        except Exception as e:
            raise AnsibleError("An error occurred:" + str(e))

    if type in ["orders", "deals"]:
        return write_to_csv(html_content, output_file_path, include_titles, type, return_string=return_string)
    elif type in ["header"]:
        return write_to_json(html_content, output_file_path, type, return_string=return_string)
    elif type in ["opt"]:
        return write_opt(input_file_path, output_file_path, include_titles, return_string=return_string)
    
    raise ValueError('Incorrect type passed. Allowed value: "orders" OR "deals" OR "header" OR "opt".')

class LookupModule(LookupBase):
    # Expecting the same list of arguments as the "main" function.
    def run(self, terms, variables=None, **kwargs):
        if len(terms) < 3:
            raise AnsibleError('parse_mt_report requires exactly 3 parameters to be passed:\n1) input file path\n2) type of file: "orders"|"deals"|"header"|"opt"\n3) include titles?')
        (input_file_path, type, include_titles) = terms
        return main(input_file_path, '', include_titles, type, True)

# Testing:
# lm = LookupModule()
# print(lm.run(sys.argv[1:]))
