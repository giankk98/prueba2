from flask import Flask, request, jsonify
import xml.etree.ElementTree as ET
import requests

app = Flask(__name__)

def get_bank_info(swift_code):
    api_key = 'iif3U5ftDcRbusHr3JkM373J528x7VKx1SmaIlnL'  # Sustituye con tu clave API real
    api_url = f'https://api.api-ninjas.com/v1/swiftcode?swift={swift_code}'
    response = requests.get(api_url, headers={'X-Api-Key': api_key})
    if response.status_code == requests.codes.ok:
        data = response.json()
        if data:
            bank_name = data[0]['bank_name']
            country = data[0]['country']
            return bank_name, country
    return 'N/A', 'N/A'

@app.route("/", methods=["GET"])
def index():
    return app.send_static_file('index.html')

@app.route("/analyze", methods=["POST"])
def analyze_xml():
    xml_content = request.form["xml_input"]
    wrapped_xml_content = f"<root>{xml_content}</root>"
    try:
        root = ET.ElementTree(ET.fromstring(wrapped_xml_content)).getroot()
        ns = {
            'head': 'urn:iso:std:iso:20022:tech:xsd:head.001.001.02',
            'pacs': 'urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08'
        }
        bicfi_from = root.find('.//head:Fr/head:FIId/head:FinInstnId/head:BICFI', ns)
        bicfi_to = root.find('.//head:To/head:FIId/head:FinInstnId/head:BICFI', ns)
        biz_msg_idr = root.find('.//head:BizMsgIdr', ns)
        msg_id = root.find('.//pacs:FIToFICstmrCdtTrf/pacs:GrpHdr/pacs:MsgId', ns)
        amount = root.find('.//pacs:CdtTrfTxInf/pacs:IntrBkSttlmAmt', ns)
        debtor_name = root.find('.//pacs:Dbtr/pacs:Nm', ns)
        creditor_name = root.find('.//pacs:Cdtr/pacs:Nm', ns)
        debtor_address = root.find('.//pacs:Dbtr/pacs:PstlAdr/pacs:StrtNm', ns)
        creditor_address = root.find('.//pacs:Cdtr/pacs:PstlAdr/pacs:StrtNm', ns)
        motive = root.find('.//pacs:RmtInf/pacs:Ustrd', ns)

        # Obtener información del banco emisor y receptor usando la función get_bank_info
        bank_from, country_from = get_bank_info(bicfi_from.text) if bicfi_from is not None else ('N/A', 'N/A')
        bank_to, country_to = get_bank_info(bicfi_to.text) if bicfi_to is not None else ('N/A', 'N/A')

        response_data = {
            "Banco Emisor (BICFI)": f"{bank_from} ({country_from})",
            "Banco Receptor (BICFI)": f"{bank_to} ({country_to})",
            "Referencia del giro": biz_msg_idr.text if biz_msg_idr is not None else 'N/A',
            "ID del mensaje": msg_id.text if msg_id is not None else 'N/A',
            "Monto de la transacción": f"{amount.text if amount is not None else 'N/A'} {amount.attrib['Ccy'] if amount is not None else ''}",
            "Ordenante": debtor_name.text if debtor_name is not None else 'N/A',
            "Dirección del Ordenante": debtor_address.text if debtor_address is not None else 'N/A',
            "Nombre Beneficiario": creditor_name.text if creditor_name is not None else 'N/A',
            "Dirección del Beneficiario": creditor_address.text if creditor_address is not None else 'N/A',
            "Detalles": motive.text if motive is not None else 'N/A',
        }
        return jsonify(response_data)
    except ET.ParseError as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
