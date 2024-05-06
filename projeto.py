from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
import json

# Cria uma instância do FastAPI
app = FastAPI()


@app.get("/{id_aba}/{id_ano}")
def read_root(id_aba: str, id_ano: int, id_categoria: str = None):
    id_aba = id_aba.lower()
    if id_categoria:
        id_categoria = id_categoria.lower()
    retorno_sub_categoria = ""

    if id_aba == "processamento":
        retorno_sub_categoria = "Processamento: viniferas, americanas_e_hibridas, uvas_de_mesa ou sem_classificacao"
    elif id_aba == "importacao":
        retorno_sub_categoria = "Importação: vinhos_de_mesa, espumante, uvas_frescas, uvas_passas ou suco_de_uva"
    elif id_aba == "exportacao":
        retorno_sub_categoria = "Exportação: vinhos_de_mesa, espumante, uvas_frescas ou suco_de_uva"

    if id_aba not in ("producao", "comercializacao", "processamento", "importacao", "exportacao"):
        raise HTTPException(status_code=400, detail="o primeiro parametro deve conter producao, comercializacao, processamento, importacao ou exportacao")
    if id_ano < 1970 or id_ano > 2022:
        raise HTTPException(status_code=400, detail="o ano deve ser de 1970 a 2022")

    if id_categoria not in ("viniferas", "víniferas", "americanas_e_hibridas", "americanas_e_hibrídas",
                            "uvas_de_mesa", "sem_classificacao", "vinhos_de_mesa", "espumante", "uvas_fresca",
                            "uvas_passas", "suco_de_uva") and id_categoria:
        raise HTTPException(status_code=400, detail="Cada categoria tem uma sub_categoria especifica: " + retorno_sub_categoria)

    dados = consultar_url(id_aba, id_ano, id_categoria)

    return {dados}

def consultar_url(id_aba: str, id_ano: int, id_categoria: str = None):
    # URL do site com a tabela

    opc = ""
    if id_aba == "producao":
        opc = "opt_02"
    elif id_aba == "comercializacao":
        opc = "opt_04"
    elif id_aba == "processamento":
        opc = "opt_03"
    elif id_aba == "importacao":
        opc = "opt_05"
    elif id_aba == "exportacao":
        opc = "opt_06"

    sub_opc = ""
    if id_categoria in ("viniferas", "víniferas", "vinhos_de_mesa"):
        sub_opc = opc + "&subopcao=subopt_01"
    elif id_categoria in ("americanas_e_hibridas", "americanas_e_hibrídas", "espumante"):
        sub_opc = opc + "&subopcao=subopt_02"
    elif id_categoria in ("uvas_de_mesa", "uvas_fresca"):
        sub_opc = opc + "&subopcao=subopt_03"
    elif (id_categoria == "sem_classificacao") or (id_aba == "importacao" and id_categoria == "uvas_passas") or (id_categoria == "suco_de_uva" and id_aba == "exportacao"):
        sub_opc = opc + "&subopcao=subopt_04"
    elif id_aba == "importacao" and id_categoria == "suco_de_uva":
        sub_opc = opc + "&subopcao=subopt_05"

    url = f"http://vitibrasil.cnpuv.embrapa.br/index.php?ano={id_ano}&opcao={opc}"

    # Fazer a requisição GET
    import time
    time.sleep(10)
    response = requests.get(url)


    # Verificar se a requisição foi bem-sucedida
    if response.status_code == 200:
        # Analisar o HTML
        print("ENTROU ANALISANDO HTML")
        soup = BeautifulSoup(response.text, 'html.parser')

        table_1 = soup.find_all(class_='tb_base tb_dados')

        data = {}
        # Extrair os dados da tabela
        if id_aba in ("producao", "comercializacao", "processamento"):
            lista = []
            for table in table_1:
                lista = table.find_all('tr')
            count = 0
            atributo = ""
            for linha in lista:
                if "tb_subitem" in str(linha):
                    separar = (linha.get_text()).split("  ")
                    lista_filtrada = [elemento.strip() for elemento in separar if elemento.strip()]
                    data[atributo][lista_filtrada[0]] = lista_filtrada[1]
                if "tb_item" in str(linha):
                    separar = (linha.get_text()).split("  ")
                    lista_filtrada = [elemento.strip() for elemento in separar if elemento.strip()]
                    atributo = lista_filtrada[0]
                    data[atributo] = {"Total": lista_filtrada[1]}
                    count += 1
        else:
            linhas = []
            for table in table_1:
                linhas = table.find_all('tr')
            count = 0
            for linha in linhas:
                if count > 0:
                    linha = str(linha).replace("  ","").replace("\n", "")
                    linha = linha.replace("<tr>", "").replace("</tr>", "").replace("</td>", "")
                    formatado = linha.split("<td>")
                    data[formatado[1]] = {"Quantidade": formatado[2], "Valor": formatado[3]}
                count=1


        # Converter para JSON
        json_data = json.dumps(data, ensure_ascii=False, indent=4)
        return json_data
        # print(json_data)

        # Salvar em um arquivo ou imprimir na tela
        #with open('dados.json', 'w') as f:
        #    f.write(json_data)
        #print("JSON gerado com sucesso!")
    else:
        raise HTTPException(status_code=500, detail="erro ao analisar e extrair tabela")
