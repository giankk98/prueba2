from flask import Flask, request, render_template_string
import xml.etree.ElementTree as ET
import requests

app = Flask(__name__)

# Función para obtener información del banco usando el código SWIFT/BIC
def get_bank_info(swift_code):
    api_key = 'YOUR_API_KEY'  # Sustituye con tu clave API real
    api_url = f'https://api.api-ninjas.com/v1/swiftcode?swift={swift_code}'
    response = requests.get(api_url, headers={'X-Api-Key': api_key})
    if response.status_code == requests.codes.ok:
        data = response.json()
        if data:
            # Asumiendo que siempre hay al menos un resultado, ajusta según sea necesario
            bank_name = data[0]['bank_name']
            country = data[0]['country']
            return bank_name, country
    return 'N/A', 'N/A'  # Devuelve valores predeterminados en caso de error

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
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

            response = f"""
                <h2>Resultados del Análisis</h2>
                <p><strong>Banco Emisor (BICFI):</strong> {bank_from} ({country_from})</p>
                <p><strong>Banco Receptor (BICFI):</strong> {bank_to} ({country_to})</p>
                <p><strong>Referencia del giro:</strong> {biz_msg_idr.text if biz_msg_idr is not None else 'N/A'}</p>
                <p><strong>ID del mensaje:</strong> {msg_id.text if msg_id is not None else 'N/A'}</p>
                <p><strong>Monto de la transacción:</strong> {amount.text if amount is not None else 'N/A'} {amount.attrib['Ccy'] if amount is not None else ''}</p>
                <p><strong>Ordenante:</strong> {debtor_name.text if debtor_name is not None else 'N/A'}</p>
                <p><strong>Dirección del Ordenante:</strong> {debtor_address.text if debtor_address is not None else 'N/A'}</p>
                <p><strong>Nombre Beneficiario:</strong> {creditor_name.text if creditor_name is not None else 'N/A'}</p>
                <p><strong>Dirección del Beneficiario:</strong> {creditor_address.text if creditor_address is not None else 'N/A'}</p>
                <p><strong>Detalles:</strong> {motive.text if motive is not None else 'N/A'}</p>
            """
            return response
        except ET.ParseError as e:
            return f"""<h2>Error al procesar el XML</h2><p class="error">{str(e)}</p>"""
    else:
        return """
        <h1>Traductor XML ISO 20022</h1>
        <form id="xml_form">
            <textarea id="xml_input" name="xml_input" placeholder="Pegue el contenido XML aquí..." style="width: 100%; height: 200px;"></textarea>
            <br>
            <input type="submit" id="submit_button" value="Analizar XML">
        </form>
        <div id="result"></div>

        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
        <script>
            $(document).ready(function() {
                $('#xml_form').submit(function(event) {
                    event.preventDefault();
                    $.ajax({
                        type: 'POST',
                        url: '/',
                        data: $(this).serialize(),
                        success: function(response) {
                            $('#result').html(response);
                        },
                        error: function(xhr, status, error) {
                            console.error('Error al enviar la solicitud:', error);
                        }
                    });
                });
            });
        </script>
        """

if __name__ == "__main__":
    app.run(debug=True)
