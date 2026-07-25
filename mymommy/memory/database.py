from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from mymommy.config.settings import settings

Base = declarative_base()

class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    role = Column(String(50)) # 'user', 'assistant', 'system'
    content = Column(Text)
    tokens = Column(Integer, default=0)

class ProjectInfo(Base):
    __tablename__ = "project_info"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text)

class MemoryManager:
    def __init__(self):
        self.engine = create_engine(f"sqlite:///{settings.db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_interaction(self, role: str, content: str, tokens: int = 0):
        with self.Session() as session:
            interaction = Interaction(role=role, content=content, tokens=tokens)
            session.add(interaction)
            session.commit()

    def get_history(self, limit: int = 50):
        with self.Session() as session:
            return session.query(Interaction).order_by(Interaction.timestamp.desc()).limit(limit).all()

    def clear_history(self):
        with self.Session() as session:
            session.query(Interaction).delete()
            session.commit()

    def get_total_tokens(self) -> int:
        from sqlalchemy import func
        with self.Session() as session:
            result = session.query(func.sum(Interaction.tokens)).scalar()
            return result or 0

    def set_project_info(self, key: str, value: str):
        with self.Session() as session:
            info = session.query(ProjectInfo).filter_by(key=key).first()
            if info:
                info.value = value
            else:
                info = ProjectInfo(key=key, value=value)
                session.add(info)
            session.commit()

    def get_project_info(self, key: str) -> str | None:
        with self.Session() as session:
            info = session.query(ProjectInfo).filter_by(key=key).first()
            return info.value if info else None
