permit (principal is Identity::User, action == Billing::Action::"viewInvoice", resource is Billing::Invoice)
when { principal == resource.customer };
