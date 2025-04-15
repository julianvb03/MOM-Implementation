import logging
import sys
from src.client.mom_client import MOMClient

# Códigos ANSI para colores (para terminales compatibles)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Emojis para indicar resultados
EMOJI_PASS = "✅"
EMOJI_FAIL = "❌"

# Lista global para almacenar resultados de pruebas
test_results = []

def record_result(test_name, passed, error=None):
    test_results.append({
        "name": test_name,
        "passed": passed,
        "error": error
    })

def print_centered_table(headers, rows):
    """
    Imprime una tabla ASCII centrada.
    :param headers: Lista de encabezados.
    :param rows: Lista de filas, cada fila es una lista con los datos.
    """
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            cell_str = str(cell)
            if len(cell_str) > col_widths[i]:
                col_widths[i] = len(cell_str)
    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header_line = "|" + "|".join(f" {str(headers[i]).center(col_widths[i])} " for i in range(len(headers))) + "|"
    print(sep)
    print(header_line)
    print(sep)
    for row in rows:
        row_line = "|" + "|".join(f" {str(row[i]).center(col_widths[i])} " for i in range(len(row))) + "|"
        print(row_line)
    print(sep)

def just_pass_fail(test_name, passed):
    """
    Imprime en tiempo real solo el nombre de la prueba y si PASSED o FAILED.
    """
    if passed:
        print(f"{GREEN}[{test_name}] {EMOJI_PASS} PASSED{RESET}")
    else:
        print(f"{RED}[{test_name}] {EMOJI_FAIL} FAILED{RESET}")

# Pruebas
def test_home(client):
    test_name = "Home"
    resp = client.get_home_message()
    if resp:
        record_result(test_name, True)
        just_pass_fail(test_name, True)
    else:
        record_result(test_name, False, error="Could not retrieve home message.")
        just_pass_fail(test_name, False)

def test_login(client):
    test_name = "Login"
    resp = client.login()
    if resp:
        record_result(test_name, True)
        just_pass_fail(test_name, True)
        return True
    else:
        record_result(test_name, False, error="Login failed (no token).")
        just_pass_fail(test_name, False)
        return False

def test_subscribe(client, queue_name):
    test_name = "Subscribe"
    response = client.subscribe(queue_name, "queue")
    if response is None:
        record_result(test_name, False, error="No response received.")
        just_pass_fail(test_name, False)
    elif response.get("success") is True:
        record_result(test_name, True)
        just_pass_fail(test_name, True)
    else:
        err = response.get("message", "Unknown error")
        record_result(test_name, False, error=err)
        just_pass_fail(test_name, False)

def test_unsubscribe(client, queue_name):
    test_name = "Unsubscribe"
    response = client.unsubscribe(queue_name, "queue")
    if response is None:
        record_result(test_name, False, error="No response received.")
        just_pass_fail(test_name, False)
    elif response.get("success") is True:
        record_result(test_name, True)
        just_pass_fail(test_name, True)
    else:
        err = response.get("message", "Unknown error")
        record_result(test_name, False, error=err)
        just_pass_fail(test_name, False)

def test_send_message(client, queue_name):
    test_name = "Send Message"
    response = client.send_message(queue_name, "Hello from tests!", "queue")
    if response is None:
        record_result(test_name, False, error="No response received.")
        just_pass_fail(test_name, False)
    elif response.get("success") is True:
        record_result(test_name, True)
        just_pass_fail(test_name, True)
    else:
        err = response.get("message", "Unknown error")
        record_result(test_name, False, error=err)
        just_pass_fail(test_name, False)

def test_receive_message(client, queue_name):
    test_name = "Receive Message"
    response = client.receive_message(queue_name, "queue")
    if response is None:
        record_result(test_name, False, error="No response received.")
        just_pass_fail(test_name, False)
    elif response.get("success") is True:
        record_result(test_name, True)
        just_pass_fail(test_name, True)
    else:
        err = response.get("message", "Unknown error")
        record_result(test_name, False, error=err)
        just_pass_fail(test_name, False)

def test_protected(client):
    test_name = "Protected Resource"
    resp = client.get_protected_resource()
    if resp:
        record_result(test_name, True)
        just_pass_fail(test_name, True)
    else:
        record_result(test_name, False, error="Could not get protected resource.")
        just_pass_fail(test_name, False)

def main():
    logging.basicConfig(level=logging.INFO)
    client = MOMClient()

    # Ejecutar tests:
    test_home(client)
    
    if not test_login(client):
        sys.exit(1)
    
    # Usar la queue "queue-example" (asumida existente o configurada para tests)
    test_queue = "queue-example"
    test_subscribe(client, test_queue)
    test_unsubscribe(client, test_queue)
    test_send_message(client, test_queue)
    test_receive_message(client, test_queue)
    test_protected(client)

    # Mostrar tabla centrada de resultados
    print(f"\n{BLUE}=== TEST RESULTS ==={RESET}")
    results_table = []
    for t in test_results:
        status = "PASSED" if t["passed"] else "FAILED"
        results_table.append([t["name"], status])
    print_centered_table(["Test Name", "Result"], results_table)

    total = len(test_results)
    passed_count = sum(1 for r in test_results if r["passed"])
    print(f"\n{YELLOW}Summary: {passed_count} of {total} tests PASSED.{RESET}")

    failed_tests = [t for t in test_results if not t["passed"]]
    if failed_tests:
        print(f"\n{RED}=== DETAILS FOR FAILED TESTS ==={RESET}")
        details_table = []
        for ft in failed_tests:
            details_table.append([ft["name"], ft["error"]])
        print_centered_table(["Test Name", "Error Details"], details_table)

if __name__ == "__main__":
    main()
