from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Input, Label, Markdown
from textual.binding import Binding
from datetime import datetime
import json
import threading
import queue
import time
import webbrowser
import httpx
from pathlib import Path

from mymommy.config.settings import settings
from mymommy.sandbox.sandbox import Sandbox
from mymommy.memory.database import MemoryManager
from mymommy.models.ollama_provider import OllamaProvider
from mymommy.tools.file_tool import FileTool
from mymommy.tools.shell_tool import ShellTool
from mymommy.agent.agent import Agent
from mymommy.agent.debug_handler import DebugHandler
from mymommy.services.indexer import ProjectIndexer
from mymommy.license.service import LicenseService

class StatusPanel(Static):
    """The top panel showing status information."""
    def compose(self) -> ComposeResult:
        with Vertical(id="status-container"):
            yield Label(f"MyMommy-CLI v{settings.VERSION}", id="app-title")
            yield Horizontal(Label("Model"), Label(settings.DEFAULT_MODEL, id="status-model"), classes="status-row")
            yield Horizontal(Label("Provider"), Label("Ollama", id="status-provider"), classes="status-row")
            yield Horizontal(Label("CWD"), Label("./", id="status-cwd"), classes="status-row")
            yield Horizontal(Label("Sandbox"), Label("cwd only ✓", id="status-sandbox"), classes="status-row")
            yield Horizontal(Label("Approval"), Label("Suggest", id="status-approval"), classes="status-row")
            yield Horizontal(Label("Mode"), Label("Agent", id="status-mode"), classes="status-row")
            yield Horizontal(Label("Activity"), Label("Idle 💤", id="status-activity"), classes="status-row")
            yield Horizontal(Label("Branch"), Label("main", id="status-branch"), classes="status-row")
            yield Horizontal(Label("Memory"), Label("Project", id="status-memory"), classes="status-row")
            yield Horizontal(Label("Tokens"), Label("0 / 450 000", id="status-tokens"), classes="status-row")
            yield Horizontal(Label("License"), Label("FREE", id="status-license"), classes="status-row")

class ChatMessage(Static):
    """A widget to display a single chat message with a warm, maternal presentation."""
    def __init__(self, role: str, content: str, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        self.content = content

    def compose(self) -> ComposeResult:
        with Vertical(classes=f"message-container role-{self.role}"):
            display_role = "MOMMY 💖" if self.role in ("assistant", "mommy") else self.role.upper()
            yield Label(f"{display_role} >", classes="message-role")
            yield Markdown(self.content, classes="message-content")

class MyMommyApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_history", "Clear", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.sandbox = Sandbox()
        self.memory = MemoryManager()
        self.model = OllamaProvider()
        self.tools = [
            FileTool(self.sandbox),
            ShellTool(self.sandbox)
        ]
        self.agent = Agent(self.model, self.tools, self.memory, self.sandbox)
        self.indexer = ProjectIndexer(self.sandbox)
        self.license_service = LicenseService()
        self.debug_handler = DebugHandler(self.agent, ShellTool(self.sandbox))
        self.chat_queue = queue.Queue()
        self.app_mode = "Agent"
        self.pending_approval = None
        self.free_limit_exceeded = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield StatusPanel(id="status-panel")
            with Vertical(id="chat-area"):
                yield ScrollableContainer(id="chat-history")
                yield Input(placeholder="Ask MyMommy anything...", id="chat-input")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#chat-input").focus()
        self.update_status()
        self.set_interval(0.1, self.poll_agent_output)

        # Welcome message in Portuguese with warm Mommy personality!
        history_container = self.query_one("#chat-history")
        history_container.mount(ChatMessage(
            role="mommy",
            content="""### Olá, meu querido! Ou minha querida! 💕
A mamãe está tão feliz em ver você por aqui! Eu já arrumei tudo na nossa casa digital e estou prontinha para ajudar você com qualquer código, bug chato, ou criação de projeto!

Digite `/help` para ver os mimos de comandos que eu preparei com tanto carinho para você, ou me faça uma pergunta técnica! Sinta-se confortável, meu bem! 😘"""
        ))

    def update_status(self):
        # Determine license & tokens
        is_pro = self.license_service.is_pro()
        license_type = "PRO" if is_pro else "FREE"
        
        tokens = self.memory.get_total_tokens()
        token_limit = "Unlimited" if is_pro else f"{settings.FREE_TOKEN_LIMIT}"
        
        if not is_pro and tokens >= settings.FREE_TOKEN_LIMIT:
            self.free_limit_exceeded = True
        else:
            self.free_limit_exceeded = False

        # Get active branch
        import git
        try:
            repo = git.Repo(self.sandbox.base_path, search_parent_directories=True)
            branch = repo.active_branch.name
        except Exception:
            branch = "main"

        try:
            self.query_one("#status-model").update(self.agent.model.model_name)
            self.query_one("#status-approval").update(self.agent.approval_mode)
            self.query_one("#status-mode").update(self.app_mode)
            self.query_one("#status-branch").update(branch)
            self.query_one("#status-tokens").update(f"{tokens} / {token_limit}")
            self.query_one("#status-license").update(license_type)
        except Exception:
            pass

    def set_activity(self, activity: str):
        try:
            self.query_one("#status-activity").update(activity)
        except Exception:
            pass

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_text = event.value.strip()
        if not user_text:
            return

        event.input.value = ""
        history_container = self.query_one("#chat-history")
        
        # Add user message to history
        history_container.mount(ChatMessage(role="user", content=user_text))
        history_container.scroll_end()

        # Check for free limit block
        if self.free_limit_exceeded and not user_text.startswith("/"):
            history_container.mount(ChatMessage(
                role="mommy",
                content="""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### ⚠️ Oh, meu bem... Nosso limite gratuito acabou!

Como sua mamãe que quer o seu melhor, eu adoraria poder trabalhar com você para sempre sem limites! 

Adquira a versão **MyMommy PRO** para liberar o seu potencial:
- ✨ Tokens ilimitados para o modelo local
- 🛠️ Autonomia sem qualquer bloqueio
- 🌟 Novas ferramentas e atualizações para a vida toda!

**Preço: R$100 (PIX)**

Para adquirir agora mesmo com aprovação automática, digite:
`/license buy`
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
            ))
            history_container.scroll_end()
            return

        # Handle slash command
        if user_text.startswith("/"):
            if self.handle_command(user_text):
                return

        # Start agent execution in background
        self.app_mode = "Agent"
        self.set_activity("Thinking 🧠")
        self.update_status()
        threading.Thread(target=self.run_agent, args=(user_text,), daemon=True).start()

    def run_agent(self, user_text: str):
        try:
            for response in self.agent.chat(user_text):
                self.chat_queue.put(response)
        except Exception as e:
            self.chat_queue.put({"type": "error", "content": str(e)})

    def poll_agent_output(self):
        history_container = self.query_one("#chat-history")
        has_new = False
        
        while not self.chat_queue.empty():
            msg = self.chat_queue.get()
            has_new = True
            
            if msg["type"] == "thought":
                # Stream thought content to the last assistant message, or create a new one
                last_msg = history_container.query(ChatMessage).last()
                if last_msg and last_msg.role in ("assistant", "mommy"):
                    last_msg.content += msg["content"]
                    last_msg.query_one(Markdown).update(last_msg.content)
                else:
                    new_msg = ChatMessage(role="mommy", content=msg["content"])
                    history_container.mount(new_msg)
            
            elif msg["type"] == "tool_approval_request":
                self.pending_approval = msg
                self.set_activity("Waiting Approved ⏳")
                history_container.mount(ChatMessage(
                    role="mommy",
                    content=f"""### ⚠️ Filhinho, posso fazer isso?
A mamãe gostaria de rodar a ferramenta **{msg['tool']}** com esses parâmetros para você:
```json
{json.dumps(msg['parameters'], indent=2)}
```
Para permitir que eu faça isso por você, digite `/approve`. Para bloquear, digite `/deny`."""
                ))
            
            elif msg["type"] == "tool_call":
                self.set_activity("Running Tool ⚙️")
                history_container.mount(ChatMessage(role="tool", content=f"⚙️ {msg['content']}"))
            
            elif msg["type"] == "tool_result":
                self.set_activity("Thinking 🧠")
                succeeded = msg.get("success", True)
                prefix = "✅" if succeeded else "❌"
                role = "result" if succeeded else "error"
                history_container.mount(ChatMessage(role=role, content=f"{prefix} {msg['content']}"))
            
            elif msg["type"] == "final_response":
                self.set_activity("Idle 💤")
                self.update_status()
            
            elif msg["type"] == "error":
                self.set_activity("Idle 💤")
                history_container.mount(ChatMessage(role="error", content=f"❌ Erro: {msg['content']}"))
            
        if has_new:
            history_container.scroll_end()

    def handle_command(self, user_text: str) -> bool:
        parts = user_text.split()
        cmd = parts[0].lower()
        args = parts[1:]
        history_container = self.query_one("#chat-history")

        if cmd == "/help":
            history_container.mount(ChatMessage(
                role="mommy",
                content="""### 📋 Comandos fofos da mamãe para você:
- `/help` : Exibe este carinhoso menu de ajuda.
- `/debug` : A mamãe executa seus testes, pega o erro de colinho e corrige tudo para você!
- `/model <nome>` : Altera o modelo configurado no Ollama.
- `/tools` : Lista as ferramentas disponíveis no sandbox.
- `/memory` : Exibe arquivos indexados e informações do projeto.
- `/license` : Informações da sua licença ativa.
- `/license buy` : Inicia o checkout PIX Mercado Pago automático para ativar o PRO.
- `/tokens` : Mostra os tokens consumidos e o limite atual.
- `/status` : Status detalhado de todos os subsistemas.
- `/plan` : Mostra os passos propostos para execução do plano atual.
- `/reset` : Limpa todo o nosso histórico local de carinhos e mensagens.
- `/approve` : Permite que a mamãe execute a ferramenta pendente.
- `/deny` : Pede para a mamãe não executar a ferramenta pendente.
- `/clear` : Limpa visualmente o terminal do chat.
- `/exit` : Fecha o MyMommy-CLI."""
            ))
            history_container.scroll_end()
            return True

        elif cmd == "/exit":
            self.exit()
            return True

        elif cmd == "/clear":
            history_container.query("*").remove()
            return True

        elif cmd == "/reset":
            self.memory.clear_history()
            history_container.query("*").remove()
            history_container.mount(ChatMessage(role="mommy", content="✅ Limpei toda a nossa lousa histórica, filhinho! Prontinhos para um novo começo."))
            self.update_status()
            history_container.scroll_end()
            return True

        elif cmd == "/tokens":
            tokens = self.memory.get_total_tokens()
            limit = "Ilimitado" if self.license_service.is_pro() else f"{settings.FREE_TOKEN_LIMIT}"
            history_container.mount(ChatMessage(
                role="mommy",
                content=f"📊 **Uso de Tokens do meu bebê:**\nConsumidos: {tokens:,} / Limite Gratuito: {limit}"
            ))
            history_container.scroll_end()
            return True

        elif cmd == "/status":
            tokens = self.memory.get_total_tokens()
            is_pro = self.license_service.is_pro()
            status_markdown = f"""### 💻 Status da sua Mommy:
- **App**: MyMommy-CLI v{settings.VERSION}
- **Modelo**: `{self.agent.model.model_name}`
- **Provider**: Ollama
- **Sandbox**: Ativo e protegido de forma maternal (Restrito a `cwd`)
- **Aprovação**: `{self.agent.approval_mode}`
- **Tokens**: {tokens:,} consumidos de forma brilhante
- **Licença**: `{'PRO (Ilimitada)' if is_pro else 'FREE (Limitada)'}`"""
            history_container.mount(ChatMessage(role="mommy", content=status_markdown))
            history_container.scroll_end()
            return True

        elif cmd == "/approve":
            if self.pending_approval:
                self.agent.approval_queue.put("approved")
                self.pending_approval = None
                self.set_activity("Thinking 🧠")
                history_container.mount(ChatMessage(role="mommy", content="✅ Obrigada pela confiança, meu bem! Executando a ferramenta agora..."))
            else:
                history_container.mount(ChatMessage(role="mommy", content="❌ Não há nada pendente para aprovar, meu anjo."))
            history_container.scroll_end()
            return True

        elif cmd == "/deny":
            if self.pending_approval:
                self.agent.approval_queue.put("denied")
                self.pending_approval = None
                self.set_activity("Idle 💤")
                history_container.mount(ChatMessage(role="mommy", content="❌ Entendido, meu bem! Guardei as ferramentas na gaveta."))
            else:
                history_container.mount(ChatMessage(role="mommy", content="❌ Não há nada pendente para negar, meu anjo."))
            history_container.scroll_end()
            return True

        elif cmd == "/tools":
            tools_list = "\n".join([f"- **{t.name}**: {t.description}" for t in self.tools])
            history_container.mount(ChatMessage(
                role="mommy",
                content=f"🛠️ **Ferramentas que a mamãe pode usar no Sandbox:**\n{tools_list}"
            ))
            history_container.scroll_end()
            return True

        elif cmd == "/model":
            if args:
                new_model = args[0]
                self.agent.model.model_name = new_model
                history_container.mount(ChatMessage(role="mommy", content=f"🤖 Modelo alterado para `{new_model}`, filhinho!"))
                self.update_status()
            else:
                history_container.mount(ChatMessage(role="mommy", content=f"🤖 Modelo atual que estou usando: `{self.agent.model.model_name}`"))
            history_container.scroll_end()
            return True

        elif cmd == "/memory":
            summary = self.indexer.get_project_summary()
            history_container.mount(ChatMessage(role="mommy", content=f"📁 **Olha o que eu achei no seu projeto, querido:**\n\n{summary}"))
            history_container.scroll_end()
            return True

        elif cmd == "/plan":
            history_container.mount(ChatMessage(
                role="mommy",
                content="""📋 **Plano de Mãe Recomendado:**
1. [✓] Ler estrutura de diretórios e validar restrições do Sandbox.
2. [✓] Indexar arquivos-chave e analisar pendências de desenvolvimento.
3. [ ] Aguardar requisições do meu filhinho/filhinha e propor correções fofas ou automáticas."""
            ))
            history_container.scroll_end()
            return True

        elif cmd == "/debug":
            self.app_mode = "Debug"
            self.set_activity("Thinking 🧠")
            self.update_status()
            history_container.mount(ChatMessage(role="mommy", content="🛠️ Iniciando nosso fluxo de depuração inteligente. Deite no colinho da mamãe e relaxe!"))
            history_container.scroll_end()
            
            # Start debug task in background
            def run_debug():
                try:
                    result = self.debug_handler.run_debug_flow()
                    if isinstance(result, str):
                        self.chat_queue.put({"type": "thought", "content": result})
                    else:
                        for chunk in result:
                            self.chat_queue.put(chunk)
                except Exception as e:
                    self.chat_queue.put({"type": "error", "content": f"Debug error: {str(e)}"})
            
            threading.Thread(target=run_debug, daemon=True).start()
            return True

        elif cmd == "/license":
            if args and args[0] == "buy":
                # Start fast checkout flow
                history_container.mount(ChatMessage(role="mommy", content="⚡ Preparando uma cobrança Pix Mercado Pago fofa para você..."))
                history_container.scroll_end()
                
                def checkout_thread():
                    try:
                        try:
                            payment_info = httpx.post(
                                f"{settings.BACKEND_URL}/license/create-payment",
                                json={"user_id": "mymommy_user_local"},
                                timeout=5.0
                            ).json()
                            payment_id = payment_info["payment_id"]
                            url = payment_info["payment_url"]
                            copy_paste = payment_info["copy_paste"]
                            is_mock = False
                        except Exception:
                            # Offline simulation mode
                            time.sleep(1)
                            payment_id = "simulated_payment_id"
                            url = "http://localhost:8000/mock-checkout"
                            copy_paste = "00020126580014br.gov.bcb.pix0136mymommypropixkey100"
                            is_mock = True
                            self.chat_queue.put({
                                "type": "thought",
                                "content": "⚠️ **Backend offline/indisponível.** Iniciando simulação local segura do fluxo de pagamento..."
                            })

                        # Show details
                        self.chat_queue.put({
                            "type": "thought",
                            "content": f"""### 💸 Detalhes do Pix MyMommy PRO:
- **Pix Copia e Cola:**
`{copy_paste}`

🔗 **A mamãe está abrindo a página de checkout simulado no seu navegador padrão...**"""
                        })
                        
                        # Open webbrowser
                        webbrowser.open(url)
                        
                        # Poll status
                        self.chat_queue.put({
                            "type": "thought",
                            "content": "⏳ *Aguardando confirmação do pagamento do Pix...*"
                        })
                        
                        approved = False
                        if is_mock:
                            # Wait 10 seconds for simulated approval
                            for i in range(10):
                                time.sleep(1)
                            approved = True
                        else:
                            # Real poll
                            for _ in range(60): # 5 minutes max
                                time.sleep(5)
                                try:
                                    status_info = httpx.get(f"{settings.BACKEND_URL}/license/status/{payment_id}").json()
                                    if status_info.get("status") == "approved":
                                        approved = True
                                        break
                                except Exception:
                                    pass
                                    
                        if approved:
                            # Activate license
                            license_data = {
                                "license_key": "PRO_MEMBER_LICENSE_VALID",
                                "plan": "PRO",
                                "user_id": "mymommy_user_local"
                            }
                            self.license_service.save_license(license_data)
                            self.chat_queue.put({
                                "type": "thought",
                                "content": """### ✨ Pix Confirmado com Sucesso!
**MyMommy PRO** está ativado! Agora temos tokens ilimitados para desenvolver tudo o que o seu coração mandar! 🚀💖"""
                            })
                            # Trigger update status event
                            self.chat_queue.put({"type": "final_response", "content": ""})
                    except Exception as e:
                        self.chat_queue.put({"type": "error", "content": f"Erro no checkout: {str(e)}"})

                threading.Thread(target=checkout_thread, daemon=True).start()
                return True
            else:
                is_pro = self.license_service.is_pro()
                status = "PRO (Ativa)" if is_pro else "FREE (Limite de 450.000 tokens)"
                info_msg = f"💳 **Licença ativa:**\nStatus: {status}\n\nPara comprar a versão PRO (R$100 vitalício) e apoiar sua Mommy, digite: `/license buy`"
                history_container.mount(ChatMessage(role="mommy", content=info_msg))
                history_container.scroll_end()
                return True

        return False

    def action_clear_history(self):
        self.handle_command("/clear")

if __name__ == "__main__":
    app = MyMommyApp()
    app.run()
