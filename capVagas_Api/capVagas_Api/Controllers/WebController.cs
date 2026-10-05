using capVagas_Api.Hubs;
using capVagas_Domain.Models;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;

namespace capVagas_Api.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class WebController : ControllerBase
    {
        private const int LIMITE_VAGAS_SITE = 100;
        private static readonly List<Vaga> vagas = new();
        private readonly IHubContext<VagaHub> hubContext;

        private static FiltroVagas filtro = new()
        {
            Palavras = new List<string>(),
            Locais = new List<string>()
        };

        public WebController(IHubContext<VagaHub> hubContext)
        {
            this.hubContext = hubContext;
        }

        [HttpPost]
        public async Task<IActionResult> Enviar([FromBody] List<Vaga> novasVagas)
        {
            if (novasVagas == null || novasVagas.Count == 0)
                return BadRequest("Nenhuma vaga recebida.");

            var vagasParaEnviar = new List<Vaga>();
            var vagasAdicionadas = 0;

            lock (vagas)
            {
                foreach (var vaga in novasVagas)
                {
                    if (vaga == null)
                        continue;

                    if (string.IsNullOrWhiteSpace(vaga.Titulo))
                        vaga.Titulo = "Não encontrado";

                    if (string.IsNullOrWhiteSpace(vaga.Empresa))
                        vaga.Empresa = "Não encontrado";

                    if (string.IsNullOrWhiteSpace(vaga.Local))
                        vaga.Local = "Rio de Janeiro";

                    if (string.IsNullOrWhiteSpace(vaga.Salario))
                        vaga.Salario = "Salário não encontrado";

                    if (string.IsNullOrWhiteSpace(vaga.Link))
                        vaga.Link = "Não encontrado";

                    if (string.IsNullOrWhiteSpace(vaga.DataPublicacao))
                        vaga.DataPublicacao = "Não encontrado";

                    if (string.IsNullOrWhiteSpace(vaga.Origem))
                        vaga.Origem = "Não encontrado";

                    if (VagaJaExiste(vaga))
                        continue;

                    vaga.DataAdicionada = DateTime.Now;

                    vagas.Add(vaga);
                    vagasAdicionadas++;

                    if (VagaPassouNoFiltro(vaga))
                        vagasParaEnviar.Add(vaga);
                }
            }

            foreach (var vaga in vagasParaEnviar)
            {
                await hubContext.Clients.All.SendAsync("NovaVaga", vaga);
            }

            return Ok(new
            {
                recebidas = novasVagas.Count,
                adicionadas = vagasAdicionadas,
                enviadasSignalR = vagasParaEnviar.Count
            });
        }

        [HttpGet]
        public IActionResult Listar()
        {
            List<Vaga> resultado;

            lock (vagas)
            {
                resultado = vagas
                    .Where(VagaPassouNoFiltro)
                    .OrderByDescending(v => v.DataAdicionada)
                    .Take(LIMITE_VAGAS_SITE)
                    .ToList();
            }

            return Ok(resultado);
        }

        [HttpGet("todas")]
        public IActionResult ListarTodas()
        {
            lock (vagas)
                return Ok(vagas.OrderByDescending(v => v.DataAdicionada) .ToList());
        }

        [HttpGet("filtro")]
        public IActionResult ObterFiltro()
        {
            return Ok(filtro);
        }

        [HttpPut("filtro")]
        public IActionResult AlterarFiltro([FromBody] FiltroVagas novoFiltro)
        {
            if (novoFiltro == null)
                return BadRequest("Filtro inválido.");

            novoFiltro.Palavras ??= new List<string>();
            novoFiltro.Locais ??= new List<string>();

            novoFiltro.Palavras = novoFiltro.Palavras
                .Where(p => !string.IsNullOrWhiteSpace(p))
                .Select(p => p.Trim())
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToList();

            novoFiltro.Locais = novoFiltro.Locais
                .Where(l => !string.IsNullOrWhiteSpace(l))
                .Select(l => l.Trim())
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToList();

            filtro = novoFiltro;

            return Ok(filtro);
        }

        private static bool VagaPassouNoFiltro(Vaga vaga)
        {
            bool passouPalavras = filtro.Palavras.Count == 0 || filtro.Palavras.Any(palavra => TextoContem(vaga.Titulo, palavra) || TextoContem(vaga.Empresa, palavra));
            bool passouLocais = filtro.Locais.Count == 0 || filtro.Locais.Any(local => TextoContem(vaga.Local, local));

            return passouPalavras && passouLocais;
        }

        private static bool TextoContem(
            string texto,
            string valor)
        {
            if (string.IsNullOrWhiteSpace(texto) || string.IsNullOrWhiteSpace(valor))
                return false;

            return texto.Contains(valor, StringComparison.OrdinalIgnoreCase);
        }

        private static bool VagaJaExiste(Vaga novaVaga)
        {
            return vagas.Any(vaga => VagasIguais(vaga, novaVaga));
        }

        private static bool VagasIguais(Vaga existente, Vaga nova)
        {
            string linkExistente = ObterLinkValido(existente);
            string linkNovo = ObterLinkValido(nova);

            if (!string.IsNullOrWhiteSpace(linkExistente) && !string.IsNullOrWhiteSpace(linkNovo))
                return linkExistente.Equals(linkNovo, StringComparison.OrdinalIgnoreCase);

            return existente.Titulo.Equals(nova.Titulo, StringComparison.OrdinalIgnoreCase) && existente.Empresa.Equals(nova.Empresa, StringComparison.OrdinalIgnoreCase) && existente.Local.Equals(nova.Local, StringComparison.OrdinalIgnoreCase);
        }

        private static string ObterLinkValido(Vaga vaga)
        {
            if (string.IsNullOrWhiteSpace(vaga.Link))
                return string.Empty;

            if (vaga.Link.Equals("Não encontrado", StringComparison.OrdinalIgnoreCase))
                return string.Empty;

            return vaga.Link.Trim().TrimEnd('/');
        }
    }
}