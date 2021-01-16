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

## 09/24/2020
#### Version 13.3.0.0.20
- [FIX] clx_task_management : change field label and set date when subtask and parent task is created from the requestform.

## 09/24/2020
#### Version 13.3.0.0.8
- [FIX] clx_invoice_reports : added missing dependency.

## 09/24/2020
#### Version 13.3.0.0.2
- [FIX] clx_budget_management : Fix the issue of budget is not creating when sale order is created from CRM.

## 09/24/2020
#### Version 13.3.0.0.9
- [FIX] clx_invoice_reports : fix the issue label printing of the month on Invoice PDF report.

## 09/24/2020
#### Version 13.3.0.0.10
- [FIX] clx_invoice_reports : fix the issue label printing of the month when year is different in invoice line on Invoice PDF report.

## 09/24/2020
#### Version 13.3.0.0.21
- [ADD] clx_task-management : make qty field readonly if category have is qty readonly checked than make qty field readonly on sale order line.

## 09/25/2020
#### Version 13.3.0.0.3
- [ADD] clx_budget_analysis_report : added column for the wholesale price on pivot report.

## 09/25/2020
#### Version 13.1.0.0.8
- [FIX] clx_invoice_policy : Invoice is not link with sale order fix that issue.
- [ADD] create invoice based on arrears policy based on sale order line.

## 09/25/2020
#### Version 13.3.0.0.21
- [ADD] clx_task_management : added chatter box on the request form view.
- [FIX] change in domain for select parent task on the sale order line. 

## 09/28/2020
#### Version 13.3.0.0.3
- [ADD] clx_budget_management : change configuration for the budget creation if end date is not set on sale order line.
- [ADD] added new action for close multiple budget line at time if budget line closed than subscription will be closed automatically.

## 09/28/2020
#### Version 13.1.1.0.3
- [FIX] clx_subscription_creation : fix the issue when sale order have end date than set end date on subscription line and budget line also.

## 09/28/2020
#### Version 13.3.0.0.22
- [FIX] clx_task_management : if client launch sub task is dependent on another main task's of sub task than create those task also create task which does sub task does not have dependency.

## 09/28/2020
#### Version 13.3.0.0.4
- [FIX] clx_budget_analysis_report : fix the issue regarding budget pivot report for upsell and downsell.

## 09/28/2020
#### Version 13.3.0.0.23
- [FIX] clx_task_management : fix some view related changes on request form.

## 09/29/2020
#### Version 13.3.0.0.5
- [FIX] clx_budget_analysis_report : changed field on pivot report. changed some fields on budget line table according to that set field on pivot report.

## 09/29/2020
#### Version 13.3.0.0.4
- [FIX] clx_budget_management : added some extra fields for calculation of the pivot report.

## 09/29/2020
#### Version 13.3.0.0.11
- [FIX] clx_invoice_reports : fixed duplicate date issue on invoice pdf report.

## 09/29/2020
#### Version 13.3.0.0.12
- [FIX] clx_invoice_reports : solved Unknown string format error. 

## 09/29/2020
#### Version 13.3.0.0.13
- [REMOVE] clx_invoice_reports : Remove extra code.

## 09/29/2020
#### Version 13.3.0.0.5
- [FIX] clx_budget_management : Fix the issue when subscription have end date.
- Filter only those date between subscription start date and end date and update only those data.

## 09/30/2020
#### Version 13.3.0.0.24
- [ADD] clx_task_management : added sale order field on request form line, filtered only active sale order.
- [ADD] Set price unit on sale order line from pricelist's field minimum price.

## 10/01/2020
#### Version 13.3.0.0.5
- [ADD] clx_budget_management : when user confirm sale order if customer type is company customer than user can confirm the sale order otherwise raise warning.

## 10/01/2020
#### Version 13.1.1.0.9
- [ADD] contact_modification : invisible some field on contacts view and added new field for ads line.

## 10/01/2020
#### Version 13.3.0.0.25
- [ADD] contact_modification : Show active subscription line on request form.
- [ADD] when user submit request form than if that customers have any active sale order than user can submit the request form otherwise raise warning.
- [ADD] When user create quotation from the crm if that crm record state is won after that user can create quotation otherwise raise warning.

## 10/05/2020
#### Version 13.3.0.0.26
- clx_task_management
    - [ADD] added some fields on request form and when creating subtask set those fields data on task records.
    - [ADD] added in logic where the current date will automatically determine due dates of +3 business days for Update tasks and +5 business days for New tasks.
    - [ADD] added stage field on sub task page in project task records.
    - [MOD] Remove “Industry” from the “Sales & Purchase” tab.
    - [ADD] Added attachments tab on request form.
    - [MOD] Changed tree view of the request form and added separate menu for request form.
- contact_modification
    - [MOD] Change menu sequence for contacts application.
    
## 10/07/2020
- clx_budget_management - 13.3.0.0.6
    - [MOD] Change warning message when confirming the sale order.
- clx_task_management - 13.3.0.0.28
    - [MOD] Change warning message when create quotation from the crm and also changed config settings message.
- contact_modification - 13.1.1.0.10
    - [MOD] Change menu sequence and some field label.
- clx_invoice_policy - 13.1.0.0.9
    - [MOD] Major changes for invoice creation. Create invoice in advance month.
        - Example
            - Invoice Policy - Adv +1. 
            - Sale order Confirm on Oct Month.
            - Product1, Start Date :  01-Nov-2020 , End Date : Not set, Price : 1000.
            - Product2, Start Date :  01-Dec-2020 , End Date : Not Set, Price : 1000
            - Invoice Created Months of Nov - Dec
            - Products1 - 2000, Invoicing Period : 1-Nov-20, 31-Dec-2020
            - Products2 - 1000, Invoicing Period : 01-Dec-2020 - 31-Dec-2020
## 10/07/2020
- [MOD] clx_task_management - Hide extra info tab in project task.
- [MOD] added domain for select only company type contacts on request form.
- [MOD] contact_modification : hide address field for individual contacts. 

## 10/12/2020
#### Version 13.3.0.0.6
- [MOD] clx_budget_analysis_report : Major changes for budget report whole data now is taken from the subscription line, previously the data was taken from the budget line table.

## 10/12/2020
#### Version 13.3.0.0.30
- [MOD] clx_task_management : added ads link field in project and also added requirements field on main task.

## 10/12/2020
#### Version 13.3.0.0.30
- [ADD] contact_modification : given delete access rights to internal user for ads link.

## 10/12/2020
#### Version 13.3.0.0.7
- [FIX] clx_budget_management : removed extra code for budget report.

## 10/12/2020
#### Version 13.3.0.0.7
- [MOD] clx_budget_analysis_report : Given access rights to temporary table for budget report.

## 10/12/2020
#### Version 13.1.1.0.4
- [FIX]  clx_subscription_creation : removed extra code when subscription is creating from upsell.

## 10/12/2020
#### Version 13.1.0.0.10
- [MOD] clx_invoice_policy : invoice selection field visible on management type contact and set that field value on child contact.

## 10/12/2020
#### Version 13.3.0.0.31
- [MOD] clx_task_management : removed sale order field from the request line and added that field on request form.
- [MOD] when user select sale order on request form based on order line request line will be created and set products from the selected sale order.

## 10/13/2020
#### Version 13.1.1.0.13
- [MOD] contact_modification : merge link contact.

## 10/13/2020
#### Version 13.3.0.0.32
- [MOD] clx_task_management : removed product field from the request line.

## 10/14/2020
#### Version 13.3.0.0.9
- [FIX] clx_budget_analysis_report : Fix the issue pivot report for the budget regarding singleton error and end date filter.

## 10/14/2020
#### Version 13.3.0.0.8
- [FIX] clx_budget_management : fix the issue when user set yearly date on budget line.

## 10/14/2020
#### Version 13.1.0.0.11
- [ADD] clx_invoice_policy : added management fees and wholesale price in account move line.

## 10/14/2020
#### Version 13.1.0.0.11
- [FIX] clx_retail_pricelist : when display management is checked than show management price on pdf report otherwise not.

## 10/14/2020
#### Version 13.3.0.0.33
- [FIX] clx_task_management : fix the issue when display active sale order.

## 10/15/2020
#### Version 13.3.0.0.33
- [ADD] clx_task_management : removed the validation when create quotation from the crm.
- [ADD] when user confirm the sale order that time system check if the sale order is created from the crm than check stage
    crm if the crm stage is won than user confirm the sale order.
- [ADD] Add new filter for show future sale order on request form.

## 10/15/2020
#### Version 13.1.1.0.5
- [ADD] clx_subscription_creation : hide the quantity fields on sale order line.

## 10/15/2020
#### Version 13.3.0.0.10
- [ADD] clx_budget_report_analysis : added filter on search view names as client.

## 10/15/2020
#### Version 13.3.0.0.15
- [ADD] added management fees on invoice report and wholesale price.

## 10/15/2020
#### Version 13.1.0.0.13
- [ADD] clx_invoice_policy : Added wholesale price and management price on invoice line for display on the invoice pdf report.

## 10/20/2020
#### Version 13.1.0.0.14
- [ADD] clx_invoice_policy : When user confirm the sale order invoice is created only current month lines.
- [ADD] While creating the invoices from button added some validation for that.

## 10/20/2020
#### Version 13.1.0.0.12
- [ADD] clx_retail_pricelist : hide the quantity and price field on configurator.

## 10/20/2020
#### Version 13.3.0.0.16
- [ADD] clx_invoice_reports : added calculation for the display management fees and wholesale price

## 10/20/2020
#### Version 13.1.1.0.14
- [ADD] contact_modification : change field label.

## 10/21/2020
#### Version 13.1.0.0.15
- [MOD] clx_invoice_policy : added warning message when invoice is not generated.

## 10/21/2020
#### Version 13.3.0.0.35
- [MOD] clx_task_management : added new fields in project and also change kanban view of the project.
- [MOD] set Intended Launch Date in main task also earlier it was set only subtask only.
- [FIX] Fix timezone issue when set default time on request form field in request form.

## 10/21/2020
#### Version 13.1.1.0.15
- [Add] contact_modification : Added new fields as per new documents.

## 10/22/2020
#### Version 13.1.1.0.16
- [ADD] contact_modification : added new fields in contacts.
- [MOD] while click on projects smart button open request form records.

## 10/22/2020
#### Version 13.3.0.0.36
- [ADD] clx_task_management : added security group for user and manager and given access rights to the user as per user and manager.
- [ADD] Added related fields from the contacts to project and all subtask.
- [MOD] When quotation is created from the crm than automatically change state of the crm.

## 10/23/2020
#### Version 13.1.0.0.16
- [ADD] clx_invoice_policy : added field company management and also added group by and filter for the same.

## 10/23/2020
#### Version 13.3.0.0.37
- [ADD] clx_task_management : added category field on main task according to that added domain while selecting task from the request from.
- [Add] When user change task stage from all sub task form view than project task stage will be changed.

## 10/27/2020
#### Version 13.1.0.0.17
- [FIX] clx_invoice_policy : fix the issue when start date and end date difference is 1 month that time take 1 month price

## 10/27/2020
#### Version 13.1.1.0.6
- [MOD] clx_subscription_creation : make contract field required and added warning if start date is not set.

## 10/27/2020
#### Version 13.3.0.0.38
- [ADD] clx_task_management : added new fields on task and subtask.
- [ADD] added search view for main task and subtask.

## 10/27/2020
#### Version 13.1.0.0.18
- [FIX] clx_invoice_policy : Fix the issue do not create duplicate invoice.
- [FIX] Fix the issue date difference less than 1 month than calculate unit price per day wise.

## 10/27/2020
#### Version 13.3.0.0.39
- [ADD] clx_task_management : added icon for task management and request form.
- [MOD] Given user to add team members on subtask.

## 10/27/2020
#### Version 13.1.0.0.19
- [FIX] clx_invoice_policy : Fix the issue per day calculation when days difference less than month.

## 10/29/2020
#### Version 13.1.0.0.20
- [FIX] clx_invoice_policy : changed in the flow for set invoice start date and invoice end date on subscription line.

## 10/30/2020
#### Version 13.1.0.0.21
- [ADD] clx_invoice_policy : added new features for create invoice with data range manually.

## 11/02/2020
#### Version 13.1.0.0.22
- [FIX] clx_invoice_policy : Fix the issue related to change year when invoice is created in next period. it was set 2020 year it should set 2021 year.

## 11/02/2020
#### Version 13.1.0.0.1
- [Add] clx_ratio_invoice : added module for co-op.

## 11/03/2020
#### Version 13.1.0.0.23
- [MOD] clx_invoice_policy : changes for invoice creation flow when sale oreder co-op configuration is checked.

## 11/03/2020
#### Version 13.1.0.0.2
- [Add] clx_ratio_invoice : added smart button and written method for create invoice based on partner ratio.

## 11/03/2020
#### Version 13.1.1.0.7
- [ADD] clx_subscription_creation : added code for create subscriptions based on added ratio partner on sale order.

## 11/03/2020
#### Version 13.3.0.0.40
- [MOD] clx_task_management : given selection to select multiple team on main task and subtask as well changes on project task.
- [MOD] Menu changes for the projects app.

## 11/04/2020
#### Version 13.3.0.0.41
- [MOD] clx_task_management : added tag ids field on main task and set that tags into subtask.

## 11/04/2020
#### Version 13.1.1.0.8
- [ADD] clx_subscription_creation : update invoice start date and end date when user add end date on sale order line.

## 11/04/2020
#### Version 13.1.0.0.3
- [ADD] clx_ratio_invoice : added code for calculated all subscription when the sale order is ratio type also according to that return view.

## 11/04/2020
#### Version 13.1.0.0.24
- [ADD] clx_invoice_policy : added features for create arreas invoice for co-op sale order. 

## 11/06/2020
#### Version 13.3.0.0.42
- [ADD] clx_task_management : added ads link on all subtask and parent task.
- [ADD] Added new state for the project manage the state based on project manager.
- [FIX] Fix the issue related to onchange on request form.

## 11/06/2020
#### Version 13.1.1.0.17
- [ADD] contact_modification : set default US country while creating a contacts.

## 11/06/2020
#### Version 13.0.2.0.1
- [ADD] mail_debrand : added module for mail debranding.

## 11/07/2020
#### Version 13.3.0.0.43
- [FIX] clx_task_management : fix the issue when create sub task when dependent task is completed.

## 11/07/2020
#### Version 13.3.0.0.17
- [ADD] clx_invoice_reports : added new template for the contract.

## 11/10/2020
#### Version 13.3.0.0.43
- [FIX] clx_task_management : fix the issue related to request form when user select task changed in domain.
- [FIX] fix the issue of the tag on parent task and subtask.removed related field and replace with normal field.

## 11/10/2020
#### Version 13.3.0.0.18
- [ADD] clx_invoice_reports : added logo and design for the contract template.

## 11/11/2020
#### Version 13.3.0.0.44
- [MOD] clx_task_management : changed field label and view related changes for the project and project task.

## 11/11/2020
#### Version 13.1.1.0.18
- [MOD] contact_modification : hide account manager field.

## 11/11/2020
#### Version 13.3.0.0.19
- [ADD] clx_invoice_reports : added report for contract with all the details(The Blake- Not Greystar).

## 11/23/2020
#### Version 13.3.0.0.45
- [MOD] clx_task_management : Prevent Projects from being marked complete until all tasks within it are done. 
- [MOD] Add the person who submitted the request form (which may be different than the salesperson). This is the person who should receive notifications, as opposed to the Salesperson. Record this field as “Submitted by”.
- [MOD] Added deadline on project.

## 11/23/2020
#### Version 13.1.0.0.25
- [FIX] clx_invoice_policy : fix the issue of the invoice amount calculation.

## 11/24/2020
#### Version 13.3.0.0.46
- [FIX] clx_task_management : set team members based on team.
- [ADD] Bring the CallRail Destination Number field from the Client Setup tab of a Customer Company into the Extra Info tab of Tasks. Add this field below Google Analytics CL Account Location field.
- [ADD] Bring the DNI String field from the Client Setup tab of a Customer Company into the Extra Info tab of Tasks. Add this field below Google Analytics CL Account Location field.
- [ADD] added Review Assignment tab.  

## 11/24/2020
#### Version 13.1.1.0.19
- [FIX] contact_modification : added some fields on partner.

## 11/24/2020
#### Version 13.3.0.0.20
- [FIX] clx_invoice_reports : added taxes on pdf reports.

## 11/24/2020
#### Version 13.1.0.0.26
- [FIX] clx_invoice_policy : fix the label printing issue on invoice 

## 11/25/2020
#### Version 13.3.0.0.21 
- [ADD clx_invoice_reports : added new contract report with greystar company.

## 11/25/2020
#### Version 13.1.0.0.27
- [FIX] clx_invoice_policy : fix the issue of label printing and calculation of the amount when order is in days.

## 11/26/2020
#### Version 13.1.0.0.27
- [FIX] clx_invoice_policy : fix the issue regarding cancel invoice and regenerate the cancel invoice.

## 11/27/2020
#### Version 13.1.1.0.20
- [ADD] contact_modification : added Submittal Platform field in customer.
- [ADD] added invoice template fields.

## 11/27/2020
#### Version 13.3.0.0.46
- [FIX] clx_task_management : added activity view for all main task.

## 11/27/2020
#### Version 13.0.1.0.2
- [ADD] schedule_activity : Initial commit for the schedule activity dashboards.

## 11/30/2020
#### Version 13.3.0.0.48
- [FIX] clx_task_management : set deadline automatically on project.and set deadline on task when completed one task.

## 11/30/2020
#### Version 13.1.1.0.9
- [ADD] clx_subscription_creation : raised warning when doing upsell if price is 0 than raised warning.

## 11/30/2020
#### Version 13.1.0.0.29
- [FIX] clx_invoice_policy : fix the issue of category wise line merge when invoice is generating.

## 12/01/2020
#### Version 13.1.1.0.10
- [ADD] clx_subscription_creation : when sale order deleted than subscription will be deleted.

## 12/01/2020
#### Version 13.3.0.0.49
- [FIX] clx_task_management : set team members on all sub task.

## 12/02/2020
#### Version 13.3.0.0.50
- [FIX] clx_task_management : added conditions for the when task have multiple dependency
- [FIX] Fix the issue related tags on all task tree view.
- [ADD] Added warning when done project and parent task.

## 12/02/2020
#### Version 13.3.0.0.51
- [FIX] clx_task_management : added deadline in list view in project.

## 12/02/2020
#### Version 13.1.1.0.21
- [FIX] contact_modification : changed field type Submittal type.

## 12/03/2020
#### Version 13.3.0.0.51
- [FIX] clx_task_management : make readonly field on request form.

## 12/03/2020
#### Version 13.3.0.0.22
- [FIX] clx_invoice_reports : added tax on invoice reports.

## 12/03/2020
#### Version 13.3.0.0.23
- [FIX] clx_invoice_reports : removed extra space from invoice pdf reports.

## 12/04/2020
#### Version 13.3.0.0.24
- [FIX] clx_invoice_reports : added condition for the when print city in invoice pdf reports.

## 12/04/2020
#### Version 13.3.0.0.53
- [FIX] clx_task_management : added logic for the task not created untill the dependent task are not completed.

## 12/04/2020
#### Version 13.1.0.0.30
- [FIX] clx_invoice_policy : fix the issue of re-create invoice for the cancel invoices. 

## 12/05/2020
#### Version 13.3.0.0.25
- [FIX] clx_invoice_reports : added setup fees field on product and added that field on contract report.

## 12/05/2020
#### Version 13.3.0.0.25
- [FIX] contact_modification : added discount field on management company based on that added discount on sale order line.

## 12/05/2020
#### Version 13.1.1.0.11
- [FIX] clx_subscription_creation : added onchange for set discount on sale order line.

## 12/05/2020
#### Version 13.1.0.0.31
- [FIX] clx_invoice_policy : added discount when creating invoice.

## 12/07/2020
#### Version 13.1.0.0.32
- [FIX] clx_invoice_policy : added logic for the yearly subscription.

## 12/07/2020
#### Version 13.3.0.0.14
- [FIX] clx_budget_analysis_report : added logic for the show yearly price on pivot report.

## 12/08/2020
#### Version 13.3.0.0.15
- [FIX] clx_budget_analysis_report : fix the issue of yearly subscription creation.

## 12/08/2020
#### Version 13.3.0.0.9
- [FIX] clx_budget_management : added calculation for the yearly budget line.

## 12/08/2020
#### Version 13.1.0.0.33
- [FIX] clx_invoice_policy :  added field for the subscription lines on invoices.

## 12/08/2020
#### Version 13.1.0.0.33
- [FIX] clx_subscription_creation : added warning when user delete any line from the sale order.

## 12/09/2020
#### Version 13.1.1.0.27
- [ADD] contact_modification : added client service team field on management company.

## 12/09/2020
#### Version 13.3.0.0.54
- [ADD] clx_task_management : added priority field on request form and added other field on project and task.

## 12/09/2020
#### Version 13.1.1.0.13
- [ADD] clx_subscription_creation : added product on subscription tree view.

## 12/09/2020
#### Version 13.1.0.0.13
- [MOD] clx_retail_pricelist : change update button label on sale order.

## 12/09/2020
#### Version 13.1.0.0.34
- [ADD] clx_invoice_policy : added new sequence for the greystar company management.

## 12/09/2020
#### Version 13.3.0.0.16
- [FIX] clx_budget_analysis_report : fix the issue budget pivot report.

## 12/10/2020
#### Version 13.1.0.0.35
- [ADD] clx_invoice_policy : added logic for apply flat discount on sale order and invoice and subscription.

## 12/10/2020
#### Version 13.1.1.0.14
- [ADD] clx_subscription_creation : added calculation on to apply flat discount.

## 12/10/2020
#### Version 13.3.0.0.55
- [ADD] clx_task_management : added partner_id field on tree view of all task.

## 12/10/2020
#### Version 13.1.1.0.29
- [ADD] contact_modification : added flat discount fields on partner.

## 12/11/2020
#### Version 13.3.0.0.56
- [ADD] clx_task_management : added description on all subtask.

## 12/11/2020
#### Version 13.1.0.0.36
- [ADD] clx_invoice_policy : Create cancel invoice when click on generate invoice.

## 12/14/2020
#### Version 13.1.0.0.37
- [ADD] clx_invoice_policy : fix the issue of the generate cancel invoice from the customer form views.

## 12/14/2020
#### Version 13.3.0.0.57
- [ADD] clx_task_management : added new table for subtask.

## 12/15/2020
#### Version 13.3.0.0.17
- [ADD] clx_budget_management : added a field for wrapping.

## 12/15/2020
#### Version 13.1.0.0.38
- [FIX] clx_invoice_policy : fix the bug for cancel invoice.

## 12/15/2020
#### Version 13.3.0.0.26
- [ADD] clx_invoice_reports : added new column for product is taxable or not.

## 12/15/2020
#### Version 13.3.0.0.58
- [FIX] clx_task_management : fix the issue related to domain on request form line.

## 12/16/2020
#### Version 13.3.0.0.18
- [FIX] clx_budget_analysis_report : fix the issue related to budget pivot report.

## 12/16/2020
#### Version 13.3.0.0.11
- [ADD] clx_budget_management : added new table for budget changes.

## 12/18/2020
#### Version 13.3.0.0.59
- [FIX] clx_task_management : added attachment on project and tasks and fix the issue related to client launch task.

## 12/21/2020
#### Version 13.3.0.0.60
- [FIX] clx_task_management : Fix the issue related to create depedent task when task have multiple depedency from differetn parent task.

## 12/22/2020
#### Version 13.1.1.0.15
- [ADD] clx_subscription_creation : confirm upsell sale order automatic when user do upsell.

## 12/22/2020
#### Version 13.1.0.0.14
- [ADD] clx_retail_pricelist : skip the warning minimum price when user doing upsell and downsell.

## 12/22/2020
#### Version 13.3.0.0.12
- [ADD] clx_budget_management : added price in all budget line when product have yearly subscription.

## 12/22/2020
#### Version 13.3.0.0.19
- [ADD] clx_budget_analysis_report : added price unit for yearly subscription product.

## 12/22/2020
#### Version 13.1.0.0.15
- [ADD] clx_retail_pricelist : added comment on code.

## 12/22/2020
#### Version 13.1.0.0.16
- [ADD] clx_retail_pricelist : added depedency of the sale_subscription.

## 12/22/2020
#### Version 13.1.0.0.39
- [MOD] clx_invoice_policy : Changed invoice creation flow per month.

## 12/22/2020
#### Version 13.1.0.0.40
- [MOD] clx_invoice_policy : generate separate invoice from the generate invoices button on the sale order.

## 12/22/2020
#### Version 13.3.0.0.27
- [ADD] clx_invoice_reports : changes related to designing for pdf report.

## 12/22/2020
#### Version 13.1.1.0.30
- [ADD] contact_modification : visible account manager field.

## 12/23/2020
#### Version 13.1.0.0.41
- [MOD] clx_invoice_policy : Manage the case for handling the duplicate invoices

## 12/23/2020
#### Version 13.3.0.0.27
- [ADD] clx_invoice_reports : added new field on the invoice report for budget wrapping.

## 12/23/2020
#### Version 13.1.0.0.17
- [FIX] clx_retail_pricelist : Fix the minimum value price warning for base.

## 12/23/2020
#### Version 13.1.1.0.16
- [ADD] clx_subscription_creation : added context on the field.

## 12/24/2020
#### Version 13.3.0.0.61
- [FIX] clx_task_management : fix the issue related to description on the subtask and parent task.

## 12/28/2020
#### Version 13.3.0.0.63
- [FIX] clx_task_management : added automation for the complate parent task automatically.

## 12/28/2020
#### Version 13.3.0.0.13
- [ADD] clx_budget_management : added fetures for the send mail to the user.

## 12/28/2020
#### Version 13.3.0.0.20
- [ADD] clx_budget_analysis_report : added start date and end date on pivot report.

## 12/28/2020
#### Version 13.3.0.0.64
- [FIX] clx_task_management : fix the issue related to complete task.

## 12/30/2020
#### Version 13.3.0.0.21
- [FIX] clx_budget_analysis_report : changed field label.

## 12/30/2020
#### Version 13.3.0.0.14
- [FIX] clx_budget_management : Send mail only that line which line is changed.

## 12/30/2020
#### Version 13.1.0.0.42
- [MOD] clx_invoice_policy : Changed invoice flow as per the new flow.

## 12/30/2020
#### Version 13.1.1.0.17
- [MOD] clx_subscription_creation : changed field label.

## 12/30/2020
#### Version 13.3.0.0.65
- [MOD] clx_task_management : set salesperson in sub task.

## 12/30/2020
#### Version 13.1.0.0.43
- [FIX] clx_invoice_policy : Fixed the issue related to invoice creation for specific current month. 

## 12/31/2020
#### Version 13.3.0.0.29
- [FIX] clx_invoice_reports : added 3rd and 4th line as per the document on invoice reports.

## 12/31/2020
#### Version 13.1.0.0.44
- [MOD] clx_invoice_policy : added warning user update end date on subscriptions.

## 12/31/2020
#### Version 13.3.0.0.15
- [MOD] clx_budget_management : added prorate calculation on budget changes and budget records.

## 12/31/2020
#### Version 13.3.0.0.22
- [MOD] clx_budget_analysis_report : Show only upsell and downsell lines on the pivot report added calculation for the prorate budget.

## 01/01/2021
#### Version 13.1.0.0.45
- [MOD] clx_invoice_policy : Create invoice for the yearly subscription.

## 01/01/2021
#### Version 13.3.0.0.30
- [MOD] clx_invoice_reports : changed design for the contract related reports for the sale order.

## 01/01/2021
#### Version 13.3.0.0.66
- [MOD] clx_task_management : added new field on project and task.

## 01/02/2021
#### Version 13.1.1.0.31
- [MOD] contact_modification : added new field on customers.

## 01/02/2021
#### Version 13.1.0.0.46
- [Add] clx_invoice_policy : added start date and end date on create invoices for multiple sale orders.

## 01/02/2021
#### Version 13.3.0.0.67
- [FIX] clx_task_management : fix the issue related to cancel task flow.

## 01/04/2021
#### Version 13.3.0.0.68
- [MOD] clx_task_management : Modification of the request form line view.

## 01/04/2021
#### Version 13.3.0.0.69
- [MOD] clx_task_management : Modification of the set total budget 0 if subscription is done.

## 01/05/2021
#### Version 13.3.0.0.70
- [FIX] clx_task_management : fix the issue related to onchange.

## 01/05/2021
#### Version 13.1.0.0.47
- [FIX] clx_invoice_policy : Fix the issue related end date was set wrong while doing upsell Fixed that issue.

## 01/06/2021
#### Version 13.1.0.0.48
- [FIX] clx_invoice_policy : Fix the issue related when user add end date on subscription.

## 01/06/2021
#### Version 13.3.0.0.71
- [FIX] clx_task_management : Fix the cross task depedency issue.

## 01/06/2021
#### Version 13.3.0.0.72
- [FIX] clx_task_management : removed sale order line field from the request form line instead of this added a product.

## 01/07/2021
#### Version 13.1.0.0.48
- [FIX] clx_invoice_policy : fix the issue related to upsell.

## 01/08/2021
#### Version 13.1.1.0.32
- [FIX] contact_modification : added category field on management company.

## 01/08/2021
#### Version 13.3.0.0.73
- [ADD] clx_task_management : Added some validation on request form validation and pass product from the request to task.

## 01/08/2021
#### Version 13.1.1.0.18
- [ADD] clx_subscription_creation : changed discount logic for the subscription.

## 01/08/2021
#### Version 13.3.0.0.31
- [ADD] clx_invoice_reports: changed description on contract reports.

## 01/08/2021
#### Version 13.1.0.0.50
- [FIX] clx_invoice_policy : invoice creation flow as per the month for upsell and downsell.

## 01/09/2021
#### Version 13.3.0.0.74
- [ADD] clx_task_management : fix the external id error and task duplicate error.

## 01/10/2021
#### Version 13.1.0.0.50
- [FIX] clx_invoice_policy : removed the validation of the invoice creation.

## 01/12/2021
#### Version 13.1.1.0.33
- [ADD] contact_modification : added id field on view.

## 01/12/2021
#### Version 13.1.0.0.52
- [FIX] clx_invoice_policy : Fix the issue related to yearly subscription.

## 01/12/2021
#### Version 13.3.0.0.23
- [FIX] clx_budget_analysis_report : added calculation for the wholesale price.

## 01/13/2021
#### Version 13.3.0.0.24
- [FIX] clx_budget_analysis_report : fix the wholesale price calculation.

## 01/13/2021
#### Version 13.3.0.0.17
- [FIX] clx_budget_management : added wholesale price calculation on budget records.

## 01/13/2021
#### Version 13.1.0.0.53
- [FIX] clx_invoice_policy : changed prorate logic for the invoice creation.

## 01/13/2021
#### Version 13.1.1.0.19
- [FIX] clx_subscription_creation : Delete subscriptions when user delete sale order also delete budget line as well.

## 01/13/2021
#### Version 13.3.0.0.75
- [ADD] clx_task_management : added project creation date on project

## 01/15/2021
#### Version 13.1.0.0.54
- [FIX] clx_invoice_policy : Fixed the yearly subscription issue when creation next months invoices.

## 01/15/2021
#### Version 13.3.0.0.25
- [FIX] clx_budget_analysis_report : fix the wholesale price calculation issue.

## 01/16/2021
#### Version 13.3.0.0.26
- [FIX] clx_budget_analysis_report : fix the calucation of the wholesale price when there is downsell.

## 01/16/2021
#### Version 13.1.0.0.55
- [FIX] clx_invoice_policy : added prorated line while creating manually invoices.

## 01/16/2021
#### Version 13.3.0.0.27
- [FIX] clx_budget_analysis_report : added calulation for the prorate budget.