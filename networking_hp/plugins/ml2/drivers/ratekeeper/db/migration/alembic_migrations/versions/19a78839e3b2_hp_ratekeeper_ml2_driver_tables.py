# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

"""HP Ratekeeper ML2 driver tables

Revision ID: 19a78839e3b2
Revises: None
Create Date: 2015-06-12 13:53:30.354417

"""

# revision identifiers, used by Alembic.
revision = '19a78839e3b2'
down_revision = None


from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'hp_ml2_ratekeeper_vnet_profile',
        sa.Column('vnet_id', sa.String(length=255), nullable=False),
        sa.Column('min_rate', sa.Integer(), nullable=False),
        sa.Column('max_rate', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('vnet_id')
    )

    op.create_table(
        'hp_ml2_ratekeeper_vif_profile',
        sa.Column('vif_id', sa.String(length=255), nullable=False),
        sa.Column('segment_id', sa.Integer(), nullable=False),
        sa.Column('min_rate', sa.Integer(), nullable=False),
        sa.Column('max_rate', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('vif_id')
     )

def downgrade():
    op.drop_table('hp_ml2_ratekeeper_vif_profile')
    op.drop_table('hp_ml2_ratekeeper_vnet_profile')
