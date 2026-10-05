using System;
using System.Collections.Generic;
using System.Text;

namespace capVagas_Domain.Models
{
    public class Vaga
    {
        public string Titulo { get; set; } = string.Empty;
        public string Empresa { get; set; } = string.Empty;
        public string Local { get; set; } = string.Empty;
        public string Link { get; set; } = string.Empty;
        public string DataPublicacao { get; set; } = string.Empty;
        public string Salario { get; set; } = string.Empty;
        public string Origem { get; set; } = string.Empty;
        public DateTime DataAdicionada { get; set; }
    }
}