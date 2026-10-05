const listaVagas = document.getElementById("listaVagas");
const contador = document.getElementById("contador");
const mensagem = document.getElementById("mensagem");
const campoBusca = document.getElementById("campoBusca");
const statusIndicador = document.getElementById("statusIndicador");
const statusTexto = document.getElementById("statusTexto");
const campoPalavra = document.getElementById("campoPalavra");
const botaoAdicionarPalavra = document.getElementById("botaoAdicionarPalavra");
const listaPalavras = document.getElementById("listaPalavras");
const mensagemFiltro = document.getElementById("mensagemFiltro");

const locaisFiltro = [
    "Rio de Janeiro",
    "Duque de Caxias",
    "São João de Meriti",
    "Nova Iguaçu"
];

let vagas = [];

let filtro =
{
    palavras: [],
    locais: locaisFiltro
};

async function carregarFiltro()
{
    try 
    {
        const resposta = await fetch("/api/Web/filtro");

        if (!resposta.ok)
            throw new Error("Erro ao carregar filtro.");

        const filtroApi = await resposta.json();

        filtro.palavras = filtroApi.palavras ?? [];
        filtro.locais = locaisFiltro;

        renderizarFiltros();
    }
    catch (erro)
    {
        console.error("Erro ao carregar filtro:", erro);

        filtro.locais = locaisFiltro;
        renderizarFiltros();
    }
}

async function salvarFiltroAutomaticamente() 
{
    try
    {
        const resposta = await fetch("/api/Web/filtro", {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                palavras: filtro.palavras,
                locais: locaisFiltro
            })
        });

        if (!resposta.ok)
            throw new Error("Erro ao salvar filtro.");

        const filtroApi = await resposta.json();

        filtro.palavras = filtroApi.palavras ?? [];
        filtro.locais = locaisFiltro;

        await carregarVagas();
        mostrarMensagemFiltro("Filtro atualizado.");
    } 
    catch (erro)
    {
        console.error("Erro ao salvar filtro:", erro);
        mostrarMensagemFiltro("Erro ao atualizar filtro.");
    }
}

function adicionarPalavra() 
{
    const palavra = campoPalavra.value.trim();

    if (!palavra)
        return;

    const existe = filtro.palavras.some(item => item.toLowerCase() === palavra.toLowerCase());

    if (existe)
    {
        campoPalavra.value = "";
        return;
    }

    filtro.palavras.push(palavra);
    campoPalavra.value = "";

    renderizarFiltros();
    salvarFiltroAutomaticamente();
}

function removerPalavra(index)
{
    filtro.palavras.splice(index, 1);

    renderizarFiltros();
    salvarFiltroAutomaticamente();
}

function renderizarFiltros()
{
    listaPalavras.innerHTML = "";

    filtro.palavras.forEach((palavra, index) =>
    {
        const tag = document.createElement("span");

        tag.className = "tag";

        tag.innerHTML = `
            ${escaparHtml(palavra)}
            <button type="button" onclick="removerPalavra(${index})">
                ×
            </button>
        `;

        listaPalavras.appendChild(tag);
    });
}

async function carregarVagas()
{
    try
    {
        const resposta = await fetch("/api/Web");

        if (!resposta.ok)
            throw new Error("Erro ao carregar vagas.");

        vagas = await resposta.json();

        renderizarVagas();
    }
    catch (erro)
    {
        console.error("Erro ao carregar vagas:", erro);

        contador.textContent = "Erro ao carregar as vagas.";
        mostrarMensagem("Não foi possível carregar as vagas.");
    }
}

function criarConexao()
{
    const conexao = new signalR.HubConnectionBuilder()
        .withUrl("/vagaHub")
        .withAutomaticReconnect()
        .build();

    conexao.on("NovaVaga", vaga => {
        vagas = [
            vaga,
            ...vagas.filter(v => v.link !== vaga.link)
        ].slice(0, 30);

        renderizarVagas();
    });

    conexao.onreconnecting(() => {
        statusIndicador.className = "status-off";
        statusTexto.textContent = "Reconectando...";
    });

    conexao.onreconnected(() => {
        statusIndicador.className = "status-on";
        statusTexto.textContent = "Tempo real";

        carregarVagas();
    });

    conexao.onclose(() => {
        statusIndicador.className = "status-off";
        statusTexto.textContent = "Desconectado";
    });

    iniciarConexao(conexao);
}

async function iniciarConexao(conexao)
{
    try
    {
        await conexao.start();

        statusIndicador.className = "status-on";
        statusTexto.textContent = "Conectado";
    }
    catch (erro)
    {
        console.error("Erro ao conectar ao SignalR:", erro);

        statusIndicador.className = "status-off";
        statusTexto.textContent = "Reconectando...";

        setTimeout(() => iniciarConexao(conexao), 5000);
    }
}

function renderizarVagas()
{
    const termo = campoBusca.value.toLowerCase().trim();

    const resultado = vagas.filter(vaga => {
        const titulo = (vaga.titulo || "").toLowerCase();
        const empresa = (vaga.empresa || "").toLowerCase();
        const local = (vaga.local || "").toLowerCase();
        const origem = (vaga.origem || "").toLowerCase();

        return (
            titulo.includes(termo) ||
            empresa.includes(termo) ||
            local.includes(termo) ||
            origem.includes(termo)
        );
    });

    listaVagas.innerHTML = "";

    contador.textContent =
        `${resultado.length} vaga` +
        `${resultado.length === 1 ? "" : "s"} encontrada` +
        `${resultado.length === 1 ? "" : "s"}`;

    if (resultado.length === 0) {
        mostrarMensagem("Nenhuma vaga encontrada.");
        return;
    }

    mensagem.style.display = "none";

    resultado.forEach(vaga => {
        listaVagas.appendChild(criarCard(vaga));
    });
}

function criarCard(vaga)
{
    const card = document.createElement("article");

    card.className = "vaga";

    const data = formatarData(vaga.dataAdicionada);
    const hora = formatarHora(vaga.dataAdicionada);

    card.innerHTML = `
        <div class="linha-topo">
            <span class="nova-vaga">
                VAGA NOVA ADICIONADA AS ${hora}
            </span>

            <span class="origem">
                ${escaparHtml(vaga.origem || "Não informado")}
            </span>
        </div>

        <div class="conteudo-vaga">
            <p>
                <strong>Data:</strong>
                ${data}
            </p>

            <p>
                <strong>Vaga:</strong>
                ${escaparHtml(vaga.titulo || "Não informado")}
            </p>

            <p>
                <strong>Empresa:</strong>
                ${escaparHtml(vaga.empresa || "Não informado")}
            </p>

            <p>
                <strong>Local:</strong>
                ${escaparHtml(vaga.local || "Não informado")}
            </p>

            ${vaga.salario ? `
                <p>
                    <strong>Salário:</strong>
                    ${escaparHtml(vaga.salario)}
                </p>
            ` : ""}

            ${vaga.link ? `
                <a
                    class="botao"
                    href="${escaparAtributo(vaga.link)}"
                    target="_blank"
                    rel="noopener noreferrer">
                    CLIQUE AQUI PARA ACESSAR
                </a>
            ` : ""}
        </div>
    `;

    return card;
}

function formatarData(data) 
{
    if (!data)
        return "Não informado";

    const valor = new Date(data);

    if (isNaN(valor.getTime()))
        return data;

    return valor.toLocaleDateString("pt-BR");
}

function formatarHora(data)
{
    if (!data)
        return "--:--:--";

    const valor = new Date(data);

    if (isNaN(valor.getTime()))
        return "--:--:--";

    return valor.toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
}

function mostrarMensagem(texto) 
{
    mensagem.textContent = texto;
    mensagem.style.display = "block";
}

function mostrarMensagemFiltro(texto)
{
    mensagemFiltro.textContent = texto;

    setTimeout(() =>
    {
        mensagemFiltro.textContent = "";
    }, 2000);
}

function escaparHtml(texto)
{
    const div = document.createElement("div");

    div.textContent = texto ?? "";

    return div.innerHTML;
}

function escaparAtributo(texto)
{
    return String(texto ?? "")
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

campoBusca.addEventListener("input", renderizarVagas);

botaoAdicionarPalavra.addEventListener(
    "click",
    adicionarPalavra
);

campoPalavra.addEventListener("keydown", evento => {
    if (evento.key === "Enter") {
        adicionarPalavra();
    }
});

carregarFiltro();
carregarVagas();
criarConexao();