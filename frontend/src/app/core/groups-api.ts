import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  Balance,
  Expense,
  GroupDetail,
  GroupSummary,
  Member,
  NewExpense,
  NewGroup,
  NewPayment,
  Payment,
  Settlement,
} from './api.models';

/** Calls to the backend. The dev server proxies /api to http://localhost:8000. */
@Injectable({ providedIn: 'root' })
export class GroupsApi {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/groups';

  listGroups(): Observable<GroupSummary[]> {
    return this.http.get<GroupSummary[]>(this.baseUrl);
  }

  createGroup(group: NewGroup): Observable<GroupDetail> {
    return this.http.post<GroupDetail>(this.baseUrl, group);
  }

  getGroup(groupId: number): Observable<GroupDetail> {
    return this.http.get<GroupDetail>(`${this.baseUrl}/${groupId}`);
  }

  addMember(groupId: number, name: string): Observable<Member> {
    return this.http.post<Member>(`${this.baseUrl}/${groupId}/members`, { name });
  }

  createExpense(groupId: number, expense: NewExpense): Observable<Expense> {
    return this.http.post<Expense>(`${this.baseUrl}/${groupId}/expenses`, expense);
  }

  deleteExpense(groupId: number, expenseId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${groupId}/expenses/${expenseId}`);
  }

  createPayment(groupId: number, payment: NewPayment): Observable<Payment> {
    return this.http.post<Payment>(`${this.baseUrl}/${groupId}/payments`, payment);
  }

  deletePayment(groupId: number, paymentId: number): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${groupId}/payments/${paymentId}`);
  }

  getBalances(groupId: number): Observable<Balance[]> {
    return this.http.get<Balance[]>(`${this.baseUrl}/${groupId}/balances`);
  }

  getSettlements(groupId: number): Observable<Settlement[]> {
    return this.http.get<Settlement[]>(`${this.baseUrl}/${groupId}/settlements`);
  }
}
