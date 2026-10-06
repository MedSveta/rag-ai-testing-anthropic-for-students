# PhoneBook Web Project — Requirements Knowledge Base

> Source: **PhoneBook Web Project — Software Requirements Specification 2.0**  
> Approval date: **02/11/2022**  
> Target application: `https://telranedu.web.app/`
>
> This Markdown file is a source-aligned knowledge base prepared for a RAG learning project.
> Requirement IDs and requirement meaning are retained from the source SRS.
> No new product requirements are added here.

---

## 1. Project Overview

The goal of the **Phone Book** project is to provide clients with the opportunity to create a personal contact book.

This release has limited features. More features may be added over time.

### Purpose

The purpose of the source SRS is to define the requirements for the **Phone Book** website.  
The document is intended for project stakeholders, including developers and testers.

### Scope

According to the source SRS:

- Functional testing is in scope.
- External interfaces are in scope.
- Stress testing is out of scope.
- Performance testing is out of scope.
- Automation testing is out of scope.
- The PhoneBook website is compatible with **Chrome version 27 and above**.

---

## 2. Roles

The project defines two roles:

- **Manager**
- **Customer**

Abbreviations used in the source:

| Abbreviation | Meaning |
|---|---|
| M | Manager |
| C | Customer |

---

## 3. Modules and Role Capabilities

### Manager

A Manager can:

- Register a new customer.
- Authenticate a customer.
- Authorize a customer to create a contact.
- Authorize a customer to update a contact.
- Authorize a customer to delete a contact.
- Authorize a customer to delete all contacts.
- Authorize a customer to get all contacts.

### Customer

A Customer can:

- Register.
- Login.
- Logout.
- Create a new contact.
- Update a contact.
- Delete a contact.
- View all contacts.

### Module behavior

#### Registration

- Customer: can register with valid data.
- Manager: can register a customer with valid data.

#### Login

- Customer: can login with valid data after registration.
- The source also contains a Manager description stating that a manager can "registrate customer with valid data after registration". This wording is preserved as a source ambiguity and should be clarified before production use.

#### Logout

- Customer: can logout after authentication.

#### Add new contact

- Customer: can add a new contact with valid data after authentication.
- Manager: can add a new contact with valid data by customer ID.

#### Update contact

- Customer: can update an existing contact with valid data after authentication.
- Manager: can update an existing contact using `contact_ID` and customer token.

#### Delete contact

- Customer: can delete an existing contact after authentication.
- Manager: can delete an existing contact using `contact_ID` and customer token.

#### Delete all contacts

- Customer: cannot delete all contacts.
- Manager: can delete all contacts using customer token.

#### Get all contacts

- Customer: can get all contacts after authentication.
- Manager: can get all contacts using customer token.

---

## 4. Front-End Objects

### New Customer Object

The source lists:

- Email
- Password
- Registration
- Login
- Logout

### New Contact Object

The source lists:

- Name
- Last name
- Phone number
- Email
- Address
- Description
- Save
- Edit
- Delete

---

## 5. Front-End Features

### Login / Registration

- Login form for registration.
- Login form for login.

### Add

- Create new contact.

### Edit

- Edit existing contact.

### Delete

- Delete existing contact.

### Home

- Information about the application.

### About

- Information about the project.

### Contacts

- View list of contacts.

### Logout

- Logout after login.

---

# 6. Technical Requirements

## 6.1 New Customer — Email Requirements

- **T1** — Customer email - Customer email is required
- **T2** — Customer email - Email must not be blank
- **T3** — Customer email - Must contains only one @
- **T4** — Customer email - Minimum one characters before <<@>>
- **T5** — Customer email - Minimum one characters after <<@>>
- **T6** — Customer email - English only letters

---

## 6.2 New Customer — Password Requirements

- **T7** — Customer password - Customer password is required
- **T8** — Customer password - Password must not be blank
- **T9** — Customer password – One of special characters are required [@ , $ , #, ^ , & , * , ! ]
- **T10** — Customer password – Only english letters are required
- **T11** — Customer password – Minimum one letter in UpperCase is required
- **T12** — Customer password – Minimum one letter in LowCase is required
- **T13** — Customer password – Minimum one number is required
- **T14** — Customer password - Password must have minimum 8 symbols
- **T15** — Customer password - Password must have maximum 15 symbols

---

## 6.3 New Contact — Name Requirements

- **T16** — Contact Name - Contact name is required
- **T17** — Contact Name – Contact name must not be blank
- **T18** — Contact Name – Numbers are allowed
- **T19** — Contact Name – Special characters are allowed
- **T20** — Contact Name - Contact name must have minimum 1 symbol

---

## 6.4 New Contact — Last Name Requirements

- **T21** — Contact Last Name - Contact last name is required
- **T22** — Contact Last Name – Contact name must not be blank
- **T23** — Contact Last Name – Numbers are allowed
- **T24** — Contact Last Name – Special characters are allowed
- **T25** — Contact Last Name - Contact Last Name must have minimum 1 symbol

---

## 6.5 New Contact — Email Requirements

- **T26** — Contact email - Customer email is required
- **T27** — Contact email - Email must not be blank
- **T28** — Contact email - Must contains only one @
- **T29** — Contact email - Minimum one characters before <<@>>
- **T30** — Contact email - Minimum one characters after <<@>>
- **T31** — Contact email - English only letters
- **T32** — Contact Email - Contact Email should not be repeated with the email of a previously created contact

---

## 6.6 New Contact — Address Requirements

- **T33** — Contact Address - Contact address is required
- **T34** — Contact Address – Contact address must not be blank
- **T35** — Contact Address – Numbers are allowed
- **T36** — Contact Address – Special characters are allowed
- **T37** — Contact Address- Contact name must have minimum 1 symbol

---

## 6.7 New Contact — Phone Number Requirements

- **T38** — Contact Phone Number - Phone Number address is required
- **T39** — Contact Phone Number – Phone number must not be blank
- **T40** — Contact Phone Number – Phone number can only be digits
- **T41** — Contact Phone Number - Phone must have minimum 10 symbol
- **T42** — Contact Phone Number - Phone must have maximum 15 symbol
- **T43** — Contact Phone Number – Special character are not allowed
- **T44** — Contact Phone Number – Character are not allowed
- **T45** — Contact Phone Number - Contact Phone Number should not be repeated with the phone number of a previously created contact

---

## 6.8 New Contact — Description Requirements

- **T46** — Contact Description - Description is not required
- **T47** — Contact Description – Numbers are allowed
- **T48** — Contact Description – Special characters and numbers are allowed

---

## 6.9 Missing Technical Requirement IDs

The source SRS does **not** contain requirements **T49–T53**.

No replacement requirements are inferred or added.

---

## 6.10 Update Contact — Name Requirements

- **T54** — Contact Name - Contact name is required
- **T55** — Contact Name – Contact name must not be blank
- **T56** — Contact Name – Numbers are allowed
- **T57** — Contact Name – Special characters are allowed
- **T58** — Contact Name - Contact name must have minimum 1 symbol

---

## 6.11 Update Contact — Last Name Requirements

- **T59** — Contact Last Name - Contact last name is required
- **T60** — Contact Last Name – Contact last name must not be blank
- **T61** — Contact Last Name – Numbers are allowed
- **T62** — Contact Last Name – Special characters are allowed
- **T63** — Contact Last Name - Contact Last Name must have minimum 1 symbol

---

## 6.12 Update Contact — Email Requirements

- **T64** — Contact email - Customer email is required
- **T65** — Contact email - Email must not be blank
- **T66** — Contact email - Must contains only one @
- **T67** — Contact email - Minimum one characters before <<@>>
- **T68** — Contact email - Minimum one characters after <<@>>
- **T69** — Contact email - English only letters
- **T70** — Contact Email - Contact Email should not be repeated with the email of a previously created contact

---

## 6.13 Update Contact — Address Requirements

- **T71** — Contact Address - Contact address is required
- **T72** — Contact Address – Contact address must not be blank
- **T73** — Contact Address – Numbers are allowed
- **T74** — Contact Address – Special characters are allowed
- **T75** — Contact Address- Contact address must have minimum 1 symbol

---

## 6.14 Update Contact — Phone Number Requirements

- **T76** — Contact Phone Number - Phone Number address is required
- **T77** — Contact Phone Number – Phone number must not be blank
- **T78** — Contact Phone Number – Phone number can only be digits
- **T79** — Contact Phone Number - Phone must have minimum 10 symbol
- **T80** — Contact Phone Number - Phone must have maximum 15 symbol
- **T81** — Contact Phone Number – Special character are not allowed
- **T82** — Contact Phone Number – Character are not allowed
- **T83** — Contact Phone Number - Contact Phone Number should not be repeated with the phone number of a previously created contact

---

## 6.15 Update Contact — Description Requirements

- **T84** — Contact Description - Description is not required
- **T85** — Contact Description – Numbers are allowed
- **T86** — Contact Description – Special characters are allowed

---

# 7. Functional Validations

## 7.1 Registration / Login

- **F1** — If the data for registration are not valid, the system displays an error “ Wrong email or password”.
- **F2** — If the data for login are not valid, the system displays an error “ Wrong email or password” .
- **F3** — If the data for registration are not valid if the user already exists, the system displays an error “User already exists”.
- **F4** — If the data for login are not valid in case customers do not register, the system displays an error “Wrong email or password”.

---

## 7.2 Add New Contact

- **F5** — If the required field name is blank , the system displays an error “Name cannot be empty!”.
- **F6** — If the required field last name is blank , the system displays an error “Last Name cannot be empty!”.
- **F7** — If the required field email is incorrect , the system displays an error “Email not valid: must have format email!” .
- **F8** — If the required field phone number is incorrect , the system displays an error “Phone not valid: Phone number must contain only digits! And length min 10, max 15!”.
- **F9** — If the required field address is blank , the system displays an error “Address cannot be empty!”.

---

## 7.3 Update Existing Contact

- **F10** — If the required field name is blank , the system does not save not valid data to the name field.
- **F11** — If the required field last name is blank , the system does not save not valid data to the name field.
- **F12** — If the required field email is incorrect , the system does not save not valid data to the name field.
- **F13** — If the required field phone number is incorrect , the system does not save not valid data to the name field.
- **F14** — If the required field address is blank , the system does not save not valid data to the name field.

---

## 7.4 Delete Existing Contact

- **F15** — If the Manager tries to delete contact by incorrect Contact_ID, the system displays an error “Contact does not exist!”

---

## 7.5 Delete All Contacts

- **F16** — If the Manager tries to delete all contacts by incorrect token_Contact, the system displays an error “Wrong authorization token!”.

---

# 8. Interface Requirements

The source SRS states:

- User Interfaces: **None**
- Hardware Interfaces: **None**
- Software Interfaces: **None**
- Communications Interfaces: **None**

---

# 9. Non-Functional and Other Requirements

## Non-Functional Requirements

The source states: **Nil**.

## Inverse Requirements

The source states: **Nil**.

## Design Constraint

Many PhoneBook users may not have adequate computer knowledge to use the site.

Therefore:

> The system must be intuitive and easy to understand.

## Logical Database Requirements

The source states: **Nil**.

## Other Requirements

The source states: **Nil**.

## Analysis Models

The source states: **Nil**.

---
