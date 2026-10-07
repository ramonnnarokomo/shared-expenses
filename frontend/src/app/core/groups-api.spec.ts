import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { Expense, GroupSummary, NewExpense } from './api.models';
import { GroupsApi } from './groups-api';

describe('GroupsApi', () => {
  let api: GroupsApi;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(GroupsApi);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify()); // fails if a test left an unexpected request

  it('lists the groups', () => {
    const groups: GroupSummary[] = [
      { id: 1, name: 'Viaje a Asturias', currency: 'EUR', memberCount: 4, totalSpentCents: 48250 },
    ];
    let result: GroupSummary[] | undefined;

    api.listGroups().subscribe((response) => (result = response));
    const request = http.expectOne('/api/groups');
    request.flush(groups);

    expect(request.request.method).toBe('GET');
    expect(result).toEqual(groups);
  });

  it('posts a new expense with the amounts in cents', () => {
    const newExpense: NewExpense = {
      description: 'Cena',
      amountCents: 8450,
      paidBy: 1,
      split: { mode: 'equal', memberIds: [1, 2, 3] },
    };
    let result: Expense | undefined;

    api.createExpense(7, newExpense).subscribe((expense) => (result = expense));
    const request = http.expectOne('/api/groups/7/expenses');
    request.flush({ id: 10, ...newExpense, createdAt: '2026-10-02T10:00:00Z', shares: [] });

    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual(newExpense);
    expect(result?.id).toBe(10);
  });

  it('records a payment', () => {
    api.createPayment(7, { fromMemberId: 2, toMemberId: 1, amountCents: 2340 }).subscribe();
    const request = http.expectOne('/api/groups/7/payments');

    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ fromMemberId: 2, toMemberId: 1, amountCents: 2340 });
    request.flush({ id: 3, fromMemberId: 2, toMemberId: 1, amountCents: 2340, createdAt: '' });
  });

  it('deletes an expense', () => {
    api.deleteExpense(7, 10).subscribe();
    const request = http.expectOne('/api/groups/7/expenses/10');

    expect(request.request.method).toBe('DELETE');
    request.flush(null, { status: 204, statusText: 'No Content' });
  });

  it('deletes a payment', () => {
    api.deletePayment(7, 3).subscribe();
    const request = http.expectOne('/api/groups/7/payments/3');

    expect(request.request.method).toBe('DELETE');
    request.flush(null, { status: 204, statusText: 'No Content' });
  });
});
