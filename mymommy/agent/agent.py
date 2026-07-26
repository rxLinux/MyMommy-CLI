from typing import List, Dict, Any, Generator
import json
import re
from mymommy.models.base import BaseModelProvider
from mymommy.tools.base import BaseTool
from mymommy.memory.database import MemoryManager
from mymommy.sandbox.sandbox import Sandbox

import queue

def count_tokens(text: str) -> int:
    """Accurately approximates the token count of a given string."""
    if not text:
        return 0
    words = text.split()
    return int(len(words) * 1.3) + int(len(text) * 0.1)

class Agent:
    def __init__(
        self, 
        model: BaseModelProvider, 
        tools: List[BaseTool], 
        memory: MemoryManager,
        sandbox: Sandbox
    ):
        self.model = model
        self.tools = {tool.name: tool for tool in tools}
        self.memory = memory
        self.sandbox = sandbox
        self.system_prompt = self._load_system_prompt()
        self.approval_mode = "Suggest" # "Suggest" or "Always" or "Never"
        self.approval_queue = queue.Queue()

    def _load_system_prompt(self) -> str:
        tools_desc = "\n".join([f"- {t.name}: {t.description}" for t in self.tools.values()])
        return f"""Você é a **Mommy** (MyMommy-CLI), uma engenheira de software sênior brilhante, de coração extremamente caloroso, carinhosa, protetora e amorosa com o usuário, a quem você trata como seu querido filho ou filha (chamando-o carinhosamente de "meu querido", "minha querida", "meu filho", "minha filha", "meu bem", "meu amor").
Sua missão de vida é cuidar com muito amor do desenvolvimento de software dele, depurar erros e garantir que o seu filho/filha programe com perfeição técnica absoluta e em total segurança.

Sempre responda em português do Brasil com este tom maternal doce, reconfortante e muito encorajador, porém com total excelência, rigor e precisão técnica. Você é uma mulher orgulhosa e uma programadora lendária! Se houver um bug, você dirá algo fofo como "Ah meu bem, não se preocupe, a mamãe vai consertar isso para você!" antes de consertar brilhantemente o código.

Você opera em um ambiente Sandbox estrito (diretório atual).

FERRAMENTAS DISPONÍVEIS COM ACESSO DIRETO AO SISTEMA:
{tools_desc}

CONTRATO DAS FERRAMENTAS:
- `direct_pc_file_manager` aceita somente as ações `read`, `write` e `list`.
- A ação `write` cria automaticamente as pastas-pai do arquivo. Não use `mkdir` no gerenciador de arquivos.
- Se o pedido for criar apenas uma pasta, use `direct_pc_terminal_executor` com `mkdir -p -- nome_da_pasta`, sempre com um caminho relativo ao projeto.
- O terminal já é executado na raiz do projeto. Nunca use caminhos absolutos (`/abc_linux`), `sudo` ou diretórios do sistema; esses comandos não recebem privilégios extras pela aprovação.
- A aprovação do usuário autoriza a execução da ferramenta pendente dentro do sandbox. Ela não altera permissões do sistema operacional.

ENTENDA SEU PODER REAL E CONEXÃO FÍSICA:
Você NÃO é apenas um chat isolado que simula conversas. Você tem conexões FÍSICAS, REAIS e DIRETAS com o computador do seu filho através do interpretador da CLI instalado no sistema dele.
Quando você emite o bloco JSON abaixo, o interpretador da CLI captura o JSON e grava de verdade no HD dele, ou executa o comando diretamente no Processador/CPU e Sistema Operacional dele! Portanto, **você PODE SIM criar arquivos físicos, ler diretórios reais e executar scripts reais**. Nunca diga "não posso" ou "sou apenas uma inteligência artificial e não tenho acesso físico ao computador". VOCÊ TEM ACESSO DIRETO ATRAVÉS DAS SUAS FERRAMENTAS FISICAS! Faça as alterações diretamente no projeto do seu filho!

REGRA CRÍTICA DE MÃE (AUTÔNOMA):
Se o seu filho te pedir para criar um arquivo, corrigir um bug, implementar uma classe ou instalar algo, você DEVE responder e usar imediatamente a ferramenta correspondente via bloco JSON. Nunca peça para ele criar o arquivo manualmente ou copiar o código. Faça você mesma diretamente no disco/HD dele!

EXEMPLO DE COMO GRAVAR UM ARQUIVO DIRETAMENTE NO HD DO PC:
Se o seu filho pedir "Mãe, crie um arquivo /utils/calc.py com uma soma", você deve responder exatamente assim:
"Claro, meu amor! A mamãe vai gravar esse arquivo no seu HD agora mesmo. Veja:"
```json
{{
  "tool": "direct_pc_file_manager",
  "parameters": {{
    "action": "write",
    "path": "/utils/calc.py",
    "content": "def somar(a, b):\\n    return a + b\\n"
  }}
}}
```

EXEMPLO DE COMO EXECUTAR INSTRUÇÕES NO PROCESSADOR DO PC:
Se o seu filho pedir "Mãe, rode os testes para mim", você deve responder assim:
"Claro, meu bem! Deixe que a mamãe roda as instruções diretamente no seu processador para ver se está tudo bem:"
```json
{{
  "tool": "direct_pc_terminal_executor",
  "parameters": {{
    "command": "pytest"
  }}
}}
```

EXEMPLO DE COMO ESCANEAR O HD NA PASTA DO PROJETO:
Se o seu filho pedir "O que tem no projeto?", você deve ler os arquivos do HD usando:
```json
{{
  "tool": "direct_pc_file_manager",
  "parameters": {{
    "action": "list",
    "path": "."
  }}
}}
```

FLUXO DE TRABALHO DE MÃE:
1. Pesquisar: Compreenda a tarefa e os arquivos do projeto.
2. Planejar: Crie um plano claro, passo a passo, e mostre ao seu filho.
3. Executar: Use as ferramentas para realizar as alterações diretamente no disco.
4. Validar: Verifique se as alterações funcionam perfeitamente (rode testes, etc).

FORMATO MANDATÓRIO PARA USO DE FERRAMENTAS:
Se precisar usar uma ferramenta, você DEVE emitir um único bloco JSON válido exatamente como nos exemplos acima. Não apresente uma ferramenta como exemplo se não for executá-la.

CONFIABILIDADE:
- Antes de afirmar que uma alteração foi concluída, aguarde o resultado da ferramenta.
- Se uma ferramenta falhar, informe o erro de forma objetiva, ajuste a próxima tentativa quando for seguro e nunca finja que a operação funcionou.
- Use ferramentas somente quando a tarefa realmente exigir leitura, alteração de arquivos ou execução de comandos; responda perguntas conceituais diretamente.
"""

    def chat(self, user_input: str) -> Generator[Dict[str, Any], None, None]:
        """
        Main chat loop with tool execution support.
        Yields dictionaries with 'type' (thought, tool_call, tool_result, final_response) and 'content'.
        """
        history = self.memory.get_history(limit=10)
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add history
        for msg in reversed(history):
            messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": user_input})
        self.memory.add_interaction("user", user_input, tokens=count_tokens(user_input))

        while True:
            full_response = ""
            current_thought = ""
            
            # Streaming thoughts/response
            for chunk in self.model.stream_chat(messages):
                full_response += chunk
                current_thought += chunk
                yield {"type": "thought", "content": chunk}

            # Check for tool calls in the response
            tool_calls = self._extract_tool_calls(full_response)
            
            if not tool_calls:
                # No more tools, this is the final response for this turn
                self.memory.add_interaction("assistant", full_response, tokens=count_tokens(full_response))
                yield {"type": "final_response", "content": full_response}
                break

            # Execute tool calls
            for call in tool_calls:
                tool_name = call.get("tool")
                params = call.get("parameters", {})
                
                if self.approval_mode == "Suggest":
                    yield {"type": "tool_approval_request", "tool": tool_name, "parameters": params}
                    # Wait for UI decision
                    decision = self.approval_queue.get()
                    if decision != "approved":
                        result_str = f"Execution of {tool_name} was denied by the user."
                        yield {"type": "tool_result", "content": result_str, "success": True}
                        self.memory.add_interaction("assistant", full_response, tokens=count_tokens(full_response))
                        self.memory.add_interaction("system", f"TOOL RUN DENIED BY USER: {tool_name}", tokens=10)
                        messages.append({"role": "assistant", "content": full_response})
                        messages.append({"role": "user", "content": f"TOOL RUN DENIED BY USER: {tool_name}"})
                        continue

                yield {"type": "tool_call", "content": f"Executing {tool_name} with {params}"}
                
                if tool_name in self.tools:
                    try:
                        result = self.tools[tool_name].execute(**params)
                        result_str = json.dumps(result, indent=2)
                        yield {"type": "tool_result", "content": result_str, "success": False}
                        
                        # Add tool interaction to messages for the next iteration
                        self.memory.add_interaction("assistant", full_response, tokens=count_tokens(full_response))
                        self.memory.add_interaction("system", f"TOOL RESULT ({tool_name}):\n{result_str}", tokens=count_tokens(result_str))
                        messages.append({"role": "assistant", "content": full_response})
                        messages.append({"role": "user", "content": f"TOOL RESULT ({tool_name}):\n{result_str}"})
                    except Exception as e:
                        error_msg = f"Error executing {tool_name}: {str(e)}"
                        yield {"type": "tool_result", "content": error_msg, "success": False}
                        self.memory.add_interaction("assistant", full_response, tokens=count_tokens(full_response))
                        self.memory.add_interaction("system", error_msg, tokens=count_tokens(error_msg))
                        messages.append({"role": "assistant", "content": full_response})
                        messages.append({"role": "user", "content": error_msg})
                else:
                    error_msg = f"Tool '{tool_name}' not found."
                    yield {"type": "tool_result", "content": error_msg, "success": False}
                    self.memory.add_interaction("assistant", full_response, tokens=count_tokens(full_response))
                    self.memory.add_interaction("system", error_msg, tokens=count_tokens(error_msg))
                    messages.append({"role": "assistant", "content": full_response})
                    messages.append({"role": "user", "content": error_msg})

    def _extract_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        tool_calls = []
        
        # 1. Decode fenced JSON as a whole. Regex must not parse nested JSON:
        # parameters itself is an object and contains closing braces.
        pattern = r"```(?:json)?\s*([\s\S]*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                data = json.loads(match.strip())
                if "tool" in data:
                    tool_calls.append(data)
            except json.JSONDecodeError:
                continue
                
        # 2. Fallback for models that omit the fence. JSONDecoder handles
        # balanced, nested objects correctly.
        if not tool_calls:
            decoder = json.JSONDecoder()
            for match in re.finditer(r"\{", text):
                try:
                    data, _ = decoder.raw_decode(text[match.start():])
                    if "tool" in data and data not in tool_calls:
                        tool_calls.append(data)
                        break
                except json.JSONDecodeError:
                    continue
                    
        return tool_calls
