# Module Contact Modification, CLX Retail Pricelist

## 07/22/2020 Initial Version
#### Version 13.1.1.0.6
#### Initial Version
- [IMP] Contact Modification: Code cleanup

## 07/22/2020
#### Version 13.0.0.0.2
#### Setup Module
- [IMP] CLX Retail Pricelist: Code cleanup

## 07/23/2020
#### Version 13.1.1.0.7
#### Rename contact.xml -> contact_type.xml
- [IMP] Contact Modification: Rename file and added data for Billing Contact

## 07/23/2020
#### Version 13.1.1.0.8
#### Added description
- [IMP] Contact Modification: Added description for contact type object

## 07/23/2020
#### Version 13.1.0.0.3
#### Customer Pricelist
- [IMP] CLX Retail Pricelist: set pricelist if customer has 'Billing Contact' linked contact and have parent in linked contact else Public pricelist

## 07/24/2020
#### Version 13.1.0.0.4
#### Price Calculation for Custom
- [IMP] CLX Retail Pricelist: Updated lines on SO for custom values and Update call on save

## 07/24/2020
#### Version 13.1.0.0.5
#### Reset Pricelist Item Attributes
- [IMP] CLX Retail Pricelist: Reset Pricelist Item Attributes and method of SO

## 07/25/2020
#### Version 13.1.0.0.6
#### Pricelist Item Attributes on Management and Wholesale Price Computation
- [IMP] CLX Retail Pricelist: Define function, variables to manage Pricelist Item Attributes on Management and Wholesale Price Computation

## 07/25/2020
#### Version 13.1.0.0.7
#### Resolve Conflicts
- [IMP] CLX Retail Pricelist: Resolve conflicts

## 07/25/2020
#### Version 13.1.0.0.8
#### Resolve Conflicts
- [IMP] CLX Retail Pricelist: Fixed Line id issue for SO lines

## 07/25/2020
#### dev-clx-phase-2 -> Staging-Clx-test
#### Resolve Conflicts
- [FIX] Conflict Resolved

## 07/25/2020
#### Version 13.1.0.0.9
#### dev-clx-phase-2 -> Staging-Clx-test
- [FIX] Conflict Resolved

## 07/25/2020
#### Version 13.1.0.0.4
- [FIX] clx_invoice_policy : changes field label and remove check box from the wizard
,clx_budget_analysis_report : change menu and pivot report name

## 08/26/2020
#### Version 13.3.0.0.2
- [FIX] clx_invoice_reports : Fix the some validation when company don't have bank account number
 and other data
 
## 08/29/2020
#### Version 13.3.0.0.3
- [FIX] clx_invoice_reports : Fix the issue when printing date on the pdf report.

## 08/29/2020
#### Version 13.3.0.0.4
- [FIX] clx_invoice_reports : Fix the issue when printing date on the pdf report it was printing
 blank instead of data fix that issue.
 
## 08/29/2020
#### Version 13.3.0.0.5
- [FIX] clx_invoice_reports : Fix the Issue in Year printing for different year.

## 08/29/2020
#### Version 13.3.0.0.6
- [FIX] clx_invoice_reports : Remove last comma when month label is print on label

## 08/29/2020
#### Version 13.3.0.0.7
- [FIX] clx_invoice_reports : added condition for if name field on invoice line does not have date
 value and format the code
 
## 08/29/2020
#### Version 13.3.0.0.1
- [ADD] clx_task_management : Added module - clx_task_management. 

## 09/01/2020
#### Version 13.3.0.0.2
- [ADD] clx_task_management : Development for the create task and subtask when request form is
 submitted.
 
## 09/02/2020
#### Version 13.3.0.0.3
- [MOD] clx_task_management : Development for the create dependancy task when task move on complete stage.
- added demo file for task stages

## 09/03/2020
#### Version 13.3.0.0.4
- [MOD] clx_task_management : raise warning when user delete any task.
- Default Group by team wise all the task.
- set team and team members when creating task from the master table of task.
- change view when click on smart button on request form.
- set demo stage when create new proeject from the request form.

## 09/04/2020
#### Version 13.3.0.0.5
- [MOD] clx_task_management : added project and task relation on sale order line and added domain on those fields.
- User can see only those projects record which projects is not connected with any sale order and same partner as saleorder.
- added fields on project_task.
- link project and task with sale order and sale order line.

## 09/05/2020
#### Version 13.3.0.0.6
- [FIX] clx_task_management : FIX the issue of mail followers.

## 09/05/2020
#### Version 13.3.0.0.7
- [FIX] clx_task_management : Added button for project done.

## 09/05/2020
#### Version 13.3.0.0.8
- [FIX] clx_task_management : Add parent task on Subtask tree view on task management.
- [ADD] Created Separate menu for request form (Draft req Form, Submitted Req form).
- [ADD] Added checkbox to create Client launch task on request form, if checkbox is true create task of client launch under project created from the submitted request form.
- [FIX] Fix the issue of Task Kanban view is not clickable.
- [FIX] Created a kanban view for all subtasks which are displayed as "Group by Team".
- [FIX] Fix the issue of dependency for subtask.
- [ADD] Added Demo data files for Client Launch Task and Teams.

## 09/08/2020
#### Version 13.3.0.0.9
- [ADD] clx_task_management : added demo data files for master table.

## 09/09/2020
#### Version 13.3.0.0.10
- [FIX] clx_task_management : fix the issue when creating dependency task when have one task is dependent on other main task.
- [FIX] added team and team members while creating project.task

## 09/09/2020
- [REMOVE]  Remove clx_project_management module. 

## 09/10/2020
#### Version 13.3.0.0.11
- [FIX] clx_task_management : added a button for Cancel task.
- when User click on Yes from the wizard then create dependency task. and cancelled current task.
- when User click on NO then Simple cancel current task.
- added configuration for auto create sub task when user move task from the Kanban view.

## 09/10/2020
#### Version 13.3.0.0.11
- [FIX] clx_task_management : when user create task manually than system create sub task from the main task.

## 09/10/2020
#### Version 13.1.0.0.5
#### Invoice Policy
- Partner | get_advanced_sub_lines
    - To get all the lines which start in Advance month period.
    - :param lines: Subscriptions lines
    - :return: recordset after merge with advance services

- Subscription Lines | start_in_next
    - To map with invoice and service start date of to manage Advance + N
    - Amount will be calculated bases on Current month and if any service start with advance month it will consider in invoice
    - For example:    Advance + 2  Current Month August then invoice will August + September + October\n
        -      Start      - End        Amount = Total
               08/01/2020 - 10/31/2020 1000   = 3000
               09/01/2020 - 12/31/2021 500    = 1000
               10/01/2020 - 02/28/2021 300    = 0300
                                                4300
    - :return: Total number of months

## 09/15/2020
#### Version 13.1.0.0.10
- [ADD] clx_retail_pricelist : added boolean field on pricelist.
- if checked on pricelist(Display Management Fee) than set on sale order (Display Management Fee) as checked otherwise set unchecked.

## 09/15/2020
#### Version 13.3.0.0.13
- [ADD] clx_task_management : added smart button on request form for open active sale order for particular partner.
- if partner does not have any active sale order than raise warning when request type is update.
- When user click on All Task than show only all the subtask.
- from the Kanban view of the projects when user click on any project show only parent task.

## 09/16/2020
#### Version 13.3.0.0.14
- [REMOVE] clx_task_management : Remove other data files only except client launch task.

## 09/16/2020
#### Version 13.3.0.0.15
- [MOD] clx_task_management : change OPS team name with the Ops.

## 09/16/2020
#### Version 13.3.0.0.16
- [MOD] clx_task_management : added 2 new team.

## 09/16/2020
#### Version 13.3.0.0.17
- [MOD] clx_task_management : added ondelete cascade in subtask if parent task is deleted than automatically all sub tasks is deleted.

## 09/16/2020
#### Version 13.3.0.0.18
- [MOD] clx_task_management : when user delete any task based on configuration system will create dependent task otherwise not created dependent task. in both the case task will be deleted.

## 09/17/2020
#### Version 13.3.0.0.19
- [FIX] clx_task_management : fix the issue when open active sale order.
- Issue was raised because of the subscription line does not have start date.
- [ADD] added code for request form view from the portal side.

## 09/22/2020
#### Version 13.1.0.0.6
- [FIX] clx_invoice_policy : fix the issue of the label printing and optimize the code for invoice creation from the wizard.
- [MOD] contact_modification : change 2 field type char to selection timezone,vertical.
- Hide fiscal position and purchase payment terms from the customer form view.

## 09/23/2020
#### Version 13.1.1.0.2
- [ADD] clx_subscription_creation : Added contract start date field on sale order if that field have date than set default start data on sale order line otherwise set current date.

## 09/23/2020
#### Version 13.1.0.0.7
- [FIX] clx_invoice_policy : Fix the issue of the label generating when invoice is created.
- [FIX] Optimization of the code when product category wise and fix the some issue when invoice is created sale order line.
