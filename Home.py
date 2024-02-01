import streamlit as st
from fpdf import FPDF
import base64
import os
import pandas as pd
from pandas.compat._optional import import_optional_dependency
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Orçamento Chapeação e Pintura", 0, 1, "C")

    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, 0, 1, "L")
        self.ln(4)

    def chapter_body(self, body):
        self.set_font("Arial", "", 12)
        self.multi_cell(0, 10, body)
        self.ln()

def get_orcamento_itens():
    if not hasattr(st.session_state, 'orcamento_itens'):
        st.session_state.orcamento_itens = []
    return st.session_state.orcamento_itens

def criar_chave_unico(prefixo):
    return f"{prefixo}_{id(st)}"

def criar_orcamento_pdf(cliente_info, orcamento_itens, desconto, total_itens, total_final):
    pdf_path = f"Orçamento-{cliente_info['cliente']}.pdf"
    pdf = SimpleDocTemplate(pdf_path, pagesize=A4)

    pdf_elements = []

    # Adicionar logo como cabeçalho
    logo_path = './logo_orcamento.png'
    logo_width = 250
    logo_height = 50

    # Adicionar imagem ao PDF centralizada
    logo = Image(logo_path, width=logo_width, height=logo_height)
    logo.hAlign = 'CENTER'
    pdf_elements.append(logo)

    # Adicionar espaço em branco após a imagem
    pdf_elements.append(Spacer(1, 20))

    # Informações padrão no início do PDF
    pdf_elements.append(Paragraph("CAREGNATO ESTÉTICA AUTOMOTIVA", getSampleStyleSheet()['Heading1']))
    pdf_elements.append(Paragraph("CNPJ: 42.705.808/0001-14", getSampleStyleSheet()['BodyText']))
    pdf_elements.append(Paragraph("Rua Olavo Bilac, 1265", getSampleStyleSheet()['BodyText']))
    pdf_elements.append(Paragraph("Cascavel, PARANÁ, 85812-141", getSampleStyleSheet()['BodyText']))
    pdf_elements.append(Paragraph("Telefone (45) 99933-4613", getSampleStyleSheet()['BodyText']))
    pdf_elements.append(Spacer(1, 20))  # Adiciona espaço em branco

    # Adiciona informações do cliente ao PDF
    pdf_elements.append(Paragraph("Informações do Cliente", getSampleStyleSheet()['Heading2']))
    pdf_elements.append(Paragraph(f"Cliente: {cliente_info['cliente']}", getSampleStyleSheet()['BodyText']))
    pdf_elements.append(Paragraph(f"Veículo: {cliente_info['veiculo']}", getSampleStyleSheet()['BodyText']))
    pdf_elements.append(Paragraph(f"Placa: {cliente_info['placa']}", getSampleStyleSheet()['BodyText']))
    pdf_elements.append(Paragraph(f"Telefone: {cliente_info['telefone']}", getSampleStyleSheet()['BodyText']))
    pdf_elements.append(Paragraph(f"Email: {cliente_info['email']}", getSampleStyleSheet()['BodyText']))
    pdf_elements.append(Spacer(1, 20))  # Adiciona espaço em branco

    # Adiciona tabela de itens ao PDF
    produtos = [item for item in orcamento_itens if item['tipo'] == 'Peça']
    servicos = [item for item in orcamento_itens if item['tipo'] == 'Serviço']

    data_produtos = [['Quantidade', 'Nome', 'Descrição', 'Valor Unitário', 'Valor Total']]
    for item in produtos:
        quantidade = str(item.get("quantidade", ""))
        nome_item = item.get("nome", "")
        descricao = item.get("descricao", "")
        preco_unitario = "R${:.2f}".format(item.get("preco", 0))
        preco_total = "R${:.2f}".format(item.get("quantidade", 0) * item.get("preco", 0))

        # Ajuste: Limitar a descrição a 50 caracteres e adicionar quebra de linha se necessário
        descricao = descricao[:50]
        descricao_paragraph = Paragraph(descricao, getSampleStyleSheet()['BodyText'])

        data_produtos.append([quantidade, nome_item, descricao_paragraph, preco_unitario, preco_total])

    # Adiciona a tabela de produtos ao PDF
    table_produtos = Table(data_produtos, style=[
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])

    pdf_elements.append(Paragraph("Peças do Orçamento", getSampleStyleSheet()['Heading2']))
    pdf_elements.append(table_produtos)
    pdf_elements.append(Spacer(1, 20))  # Adiciona espaço em branco

    # Adiciona a tabela de serviços ao PDF
    data_servicos = [['Quantidade', 'Nome', 'Descrição', 'Valor Unitário', 'Valor Total']]
    for item in servicos:
        quantidade = str(item.get("quantidade", ""))
        nome_item = item.get("nome", "")
        descricao = item.get("descricao", "")
        preco_unitario = "R${:.2f}".format(item.get("preco", 0))
        preco_total = "R${:.2f}".format(item.get("quantidade", 0) * item.get("preco", 0))

        # Ajuste: Limitar a descrição a 50 caracteres e adicionar quebra de linha se necessário
        descricao = descricao[:50]
        descricao_paragraph = Paragraph(descricao, getSampleStyleSheet()['BodyText'])

        data_servicos.append([quantidade, nome_item, descricao_paragraph, preco_unitario, preco_total])

    # Adiciona a tabela de serviços ao PDF
    table_servicos = Table(data_servicos, style=[
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])

    pdf_elements.append(Paragraph("Serviços do Orçamento", getSampleStyleSheet()['Heading2']))
    pdf_elements.append(table_servicos)
    pdf_elements.append(Spacer(1, 20))  # Adiciona espaço em branco

    # Calcular subtotais para produtos e serviços
    subtotal_produtos = sum(item.get("quantidade", 0) * item.get("preco", 0) for item in produtos)
    subtotal_servicos = sum(item.get("quantidade", 0) * item.get("preco", 0) for item in servicos)

    # Ajuste: Adicionar o valor do desconto ao total_final
    total_final = subtotal_produtos + subtotal_servicos - desconto

    # Adicionar subtotal, desconto e total ao PDF
    pdf_elements.append(Paragraph(f"Subtotal Produtos: R${subtotal_produtos:.2f}", getSampleStyleSheet()['BodyText']))
    pdf_elements.append(Paragraph(f"Subtotal Serviços: R${subtotal_servicos:.2f}", getSampleStyleSheet()['BodyText']))

    # Adicionar desconto apenas se for maior que zero
    if desconto > 0:
        pdf_elements.append(Paragraph(f"Desconto: R${desconto:.2f}", getSampleStyleSheet()['BodyText']))

    pdf_elements.append(Paragraph(f"Total: R${total_final:.2f}", getSampleStyleSheet()['BodyText']))
    pdf_elements.append(Spacer(1, 20))  # Adiciona espaço em branco

    # Informação padrão no final do PDF
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='SmallText', parent=styles['BodyText'], fontSize=8))

    pdf_elements.append(Paragraph("ORÇAMENTO SUJEITO A ALTERAÇÃO COM AVISO PRÉVIO. QUALQUER DÚVIDA ENTRE EM CONTATO.", styles['SmallText']))

    pdf.build(pdf_elements)

    return pdf_path

def criar_orcamento_excel(df_cliente_info, orcamento_itens):
    # Adicionar informações do cliente
    df_cliente_info_final = pd.DataFrame([df_cliente_info])

    # Adicionar informações dos itens/produtos e serviços
    df_itens = pd.DataFrame(orcamento_itens)

    # Adicione a lista de serviços conforme necessário
    servicos = []  
    df_servicos = pd.DataFrame(servicos)

    # Concatenar os DataFrames
    df_orcamento = pd.concat([df_itens, df_servicos])

    # Calcular o total
    total_itens = df_itens['quantidade'] * df_itens['preco'] if 'quantidade' in df_itens.columns and 'preco' in df_itens.columns else pd.Series([0])
    total_servicos = df_servicos['quantidade'] * df_servicos['preco'] if 'quantidade' in df_servicos.columns and 'preco' in df_servicos.columns else pd.Series([0])
    total_final = total_itens.sum() + total_servicos.sum()

    # Salvar para Excel
    excel_path = 'orcamento.xlsx'
    # with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
    #     df_orcamento.to_excel(writer, sheet_name='Orçamento', index=False)
    #     df_cliente_info_final.to_excel(writer, sheet_name='Cliente', index=False)

    return excel_path, total_final

def calcular_subtotal(itens, servicos):
    subtotal = sum((item.get("quantidade", 0) * item.get("preco", 0)) if isinstance(item, dict) else 0 for item in itens)
    subtotal += sum((servico.get("quantidade", 0) * servico.get("preco", 0)) if isinstance(servico, dict) else 0 for servico in servicos)
    return subtotal

def calcular_total(itens, servicos, desconto):
    subtotal = calcular_subtotal(itens, servicos)
    total = subtotal - desconto
    return total

def reiniciar_formulario():
    st.session_state.nome = ""
    st.session_state.descricao = ""
    st.session_state.preco = 0.0
    st.session_state.quantidade = 1

def reiniciar_formulario_cliente():
    st.session_state.cliente = ""
    st.session_state.veiculo = ""
    st.session_state.placa = ""
    st.session_state.telefone = ""
    st.session_state.email = ""
    st.session_state.desconto = 0.0

def get_binary_file_downloader_html(pdf_path, file_label='File'):
    with open(pdf_path, 'rb') as f:
        data = f.read()

    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}.pdf">Download {file_label}</a>'
    return href

    with open(temp_file_path, 'rb') as f:
        data = f.read()

    os.remove(temp_file_path)

    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_label}.pdf">Download {file_label}</a>'
    return href

def main():
    st.title("Aplicação de Orçamento")

    # Adicionar Produto ou Serviço
    tipo_item = st.selectbox("Peça ou Serviço", ["Peça", "Serviço"])

    # Inicializar variáveis de estado se não estiverem inicializadas
    if 'nome' not in st.session_state:
        st.session_state.nome = ""
    if 'descricao' not in st.session_state:
        st.session_state.descricao = ""
    if 'preco' not in st.session_state:
        st.session_state.preco = 0.0
    if 'quantidade' not in st.session_state:
        st.session_state.quantidade = 1
    if 'desconto' not in st.session_state:
        st.session_state.desconto = 0.0

    # Exibindo os campos do formulário do Item
    nome = st.text_input("Nome:", key="nome_key", value=st.session_state.nome)
    descricao = st.text_area("Descrição:", key="descricao_key", value=st.session_state.descricao)
    preco = st.number_input("Valor Unitário (R$):", key="preco_key", value=st.session_state.preco)
    quantidade = st.number_input("Quantidade:", key="quantidade_key", value=st.session_state.quantidade)

    if st.button("Adicionar Peça/Serviço"):
        # Verificar se os campos do formulário foram preenchidos
        if nome and descricao and preco is not None:
            orcamento_itens = get_orcamento_itens()
            orcamento_itens.append({"tipo": tipo_item, "nome": nome, "descricao": descricao, "preco": preco, "quantidade": quantidade})
            st.session_state.orcamento_itens = orcamento_itens

            # Limpar campos do formulário
            reiniciar_formulario()

    # Exibir Itens do Orçamento
    st.header("Peças/Serviços do Orçamento")
    orcamento_itens = get_orcamento_itens()

    if orcamento_itens:
        # Criar uma lista de números correspondentes aos itens
        numeros_itens = list(range(1, len(orcamento_itens) + 1))

        for i, (numero, item) in enumerate(zip(numeros_itens, orcamento_itens), 1):
            st.write(f"{numero}. {item['nome']} ({item['tipo']}) - R${item['preco']:.2f} (x{item['quantidade']}) - Total: R${item['quantidade']*item['preco']:.2f}")

        # Remover Item
        numero_para_remover = st.selectbox("Selecione o número da peça/serviço para remover", numeros_itens)
        if st.button("Remover Item"):
            # Encontrar o item correspondente com base no número selecionado
            item_index = numero_para_remover - 1
            if 0 <= item_index < len(orcamento_itens):
                orcamento_itens.pop(item_index)
                st.session_state.orcamento_itens = orcamento_itens

    # Segundo formulário para dados do cliente
    st.header("Informações do Cliente")
    cliente = st.text_input("Cliente:")
    veiculo = st.text_input("Veiculo:")
    placa = st.text_input("Placa:")
    telefone = st.text_input("Telefone:")
    email = st.text_input("Email:")

    # Adicione um novo campo para o desconto
    desconto = st.number_input("Desconto (R$):", key="desconto_key", value=st.session_state.desconto)

    if st.button("Adicionar Informações do Cliente e Desconto"):
        df_cliente_info = {
            'cliente': cliente,
            'veiculo': veiculo,
            'placa': placa,
            'telefone': telefone,
            'email': email,
            'desconto': desconto
        }

        # Limpar campos do formulário do cliente
        reiniciar_formulario_cliente()

        # Calcular o total de itens
        total_itens = calcular_total(get_orcamento_itens(), [], desconto)

        # Criar o Excel
        orcamento_excel_path, total_excel = criar_orcamento_excel(df_cliente_info, get_orcamento_itens())

        total = total_excel-desconto
        # Informar ao usuário que o Excel foi gerado
        st.write(f"Total: R${total:.2f}")

        # Criar o PDF a partir do Excel
        orcamento_pdf_elements = criar_orcamento_pdf(df_cliente_info, get_orcamento_itens(), desconto, total_itens, total_excel)

        # Informar ao usuário que o PDF foi gerado
        st.write("Orçamento gerado com sucesso!")

        # Adicionar download do PDF
        st.markdown(get_binary_file_downloader_html(orcamento_pdf_elements, file_label='Orçamento'), unsafe_allow_html=True)
    else:
        st.warning("Adicione itens ao orçamento, informações do cliente e o desconto antes de gerar o PDF.")

        
if __name__ == "__main__":
    main()