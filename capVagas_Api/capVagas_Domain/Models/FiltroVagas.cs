using System;
using System.Collections.Generic;
using System.Text;

namespace capVagas_Domain.Models
{
    public class FiltroVagas
    {
        public List<string> Palavras { get; set; } = new();
        public List<string> Locais { get; set; } = new();
    }
}