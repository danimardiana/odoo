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
 

 

  
 






        
 