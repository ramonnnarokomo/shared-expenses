import { Pipe, PipeTransform } from '@angular/core';

import { formatMoney } from './money';

/** Usage in templates: {{ expense.amountCents | money: group.currency }} */
@Pipe({ name: 'money' })
export class MoneyPipe implements PipeTransform {
  transform(cents: number, currency: string): string {
    return formatMoney(cents, currency);
  }
}
