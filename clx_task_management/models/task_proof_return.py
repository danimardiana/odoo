from odoo import api, fields, models


class TaskProofReturn(models.Model):
    _name = "task.proof.return"
    _rec_name = "task_id"
    _description = "Task Proof Return History"

    task_id = fields.Many2one("project.task", string="Task")
    team_id = fields.Many2one("clx.team", string="Team")
    proof_return_count = fields.Integer(string="Proof Return Count", default=0)

    def create_dependent_task(self):
        task_id = self._context.get("current_task", False)
        sub_task_id = self.env["project.task"].browse(task_id)
        proof_rerurned_stge = self.env.ref("clx_task_management.clx_project_stage_6", raise_if_not_found=False)
        if proof_rerurned_stge and sub_task_id:
            sub_task_id.write({"stage_id": proof_rerurned_stge.id})
            sub_task_id.write(
                {
                    "proof_return_ids": [
                        (
                            0,
                            False,
                            {
                                "team_id": self.team_id.id,
                                "proof_return_count": sub_task_id.proof_return_count,
                            },
                        )
                    ]
                }
            )
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }

    def create_dependent_task_from_kanban(self):
        task_id = self._context.get("current_task", False)
        sub_task_id = self.env["project.task"].browse(task_id)
        proof_rerurned_stge = self.env.ref("clx_task_management.clx_project_stage_6", raise_if_not_found=False)
        if proof_rerurned_stge and sub_task_id:
            # sub_task_id.write({"stage_id": proof_rerurned_stge.id})
            sub_task_id.write(
                {
                    "proof_return_ids": [
                        (
                            0,
                            False,
                            {
                                "team_id": self.team_id.id,
                                "proof_return_count": sub_task_id.proof_return_count,
                            },
                        )
                    ]
                }
            )
