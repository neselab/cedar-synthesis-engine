permit (principal is Identity::User, action == Billing::Action::"payInvoice", resource is Billing::Invoice)
when { principal == resource.customer && resource.amount > 0 };
