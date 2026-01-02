"""Initial schema - jobs and workflow_executions

Revision ID: 001
Revises: 
Create Date: 2025-12-26 17:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create job_status enum
    job_status = postgresql.ENUM(
        'PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED',
        name='jobstatus',
        create_type=True
    )
    job_status.create(op.get_bind(), checkfirst=True)
    
    # Create workflow_state enum  
    workflow_state = postgresql.ENUM(
        'INITIALIZED', 'RESEARCHING', 'COLLECTING_DATA', 
        'TRAINING', 'EVALUATING', 'COMPLETED', 'FAILED',
        name='workflowstate',
        create_type=True
    )
    workflow_state.create(op.get_bind(), checkfirst=True)
    
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('topic', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(100), nullable=False),
        sa.Column('status', sa.Enum(
            'PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED',
            name='jobstatus'
        ), nullable=False),
        sa.Column('current_state', sa.Enum(
            'INITIALIZED', 'RESEARCHING', 'COLLECTING_DATA',
            'TRAINING', 'EVALUATING', 'COMPLETED', 'FAILED',
            name='workflowstate'
        ), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('mlflow_experiment_id', sa.String(100), nullable=True),
        sa.Column('mlflow_run_id', sa.String(100), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('max_retries', sa.Integer(), default=3),
    )
    
    # Create indexes for jobs
    op.create_index('idx_jobs_status', 'jobs', ['status'])
    op.create_index('idx_jobs_created_at', 'jobs', ['created_at'])
    
    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('iteration', sa.Integer(), nullable=False, default=0),
        sa.Column('state', sa.Enum(
            'INITIALIZED', 'RESEARCHING', 'COLLECTING_DATA',
            'TRAINING', 'EVALUATING', 'COMPLETED', 'FAILED',
            name='workflowstate'
        ), nullable=False),
        sa.Column('status', sa.Enum(
            'PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED',
            name='jobstatus'
        ), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('state_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('mlflow_run_id', sa.String(100), nullable=True),
    )
    
    # Create indexes for workflow_executions
    op.create_index('idx_workflow_executions_job_id', 'workflow_executions', ['job_id'])
    op.create_index('idx_workflow_executions_status', 'workflow_executions', ['status'])


def downgrade() -> None:
    op.drop_index('idx_workflow_executions_status')
    op.drop_index('idx_workflow_executions_job_id')
    op.drop_table('workflow_executions')
    
    op.drop_index('idx_jobs_created_at')
    op.drop_index('idx_jobs_status')
    op.drop_table('jobs')
    
    # Drop enums
    sa.Enum(name='workflowstate').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='jobstatus').drop(op.get_bind(), checkfirst=True)
