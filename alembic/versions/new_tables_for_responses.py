"""Add tables for responses

Revision ID: add_responses_tables
Revises: 2aeef0326b2a
Create Date: 2025-12-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_responses_tables'
down_revision = '2aeef0326b2a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем поля в users
    op.add_column('users', sa.Column('hh_resume_id', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('contact_email', sa.String(length=200), nullable=True))
    op.add_column('users', sa.Column('contact_phone', sa.String(length=50), nullable=True))
    
    # Создаем таблицу generated_resumes
    op.create_table('generated_resumes',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('vacancy_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('hh_resume_id', sa.String(length=100), nullable=True),
        sa.Column('is_uploaded_to_hh', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['vacancy_id'], ['vacancies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Создаем таблицу cover_letters
    op.create_table('cover_letters',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('vacancy_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['vacancy_id'], ['vacancies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Добавляем индексы
    op.create_index(op.f('ix_generated_resumes_user_id'), 'generated_resumes', ['user_id'], unique=False)
    op.create_index(op.f('ix_generated_resumes_vacancy_id'), 'generated_resumes', ['vacancy_id'], unique=False)
    op.create_index(op.f('ix_cover_letters_user_id'), 'cover_letters', ['user_id'], unique=False)
    op.create_index(op.f('ix_cover_letters_vacancy_id'), 'cover_letters', ['vacancy_id'], unique=False)


def downgrade() -> None:
    # Удаляем таблицы и поля
    op.drop_index(op.f('ix_cover_letters_vacancy_id'), table_name='cover_letters')
    op.drop_index(op.f('ix_cover_letters_user_id'), table_name='cover_letters')
    op.drop_index(op.f('ix_generated_resumes_vacancy_id'), table_name='generated_resumes')
    op.drop_index(op.f('ix_generated_resumes_user_id'), table_name='generated_resumes')
    
    op.drop_table('cover_letters')
    op.drop_table('generated_resumes')
    
    op.drop_column('users', 'contact_phone')
    op.drop_column('users', 'contact_email')
    op.drop_column('users', 'hh_resume_id')