import { Routes } from '@angular/router';

import { GroupDetailPage } from './group-detail/group-detail-page';
import { GroupsPage } from './groups/groups-page';

export const routes: Routes = [
  { path: '', component: GroupsPage, title: 'Grupos · Gastos compartidos' },
  { path: 'groups/:id', component: GroupDetailPage, title: 'Grupo · Gastos compartidos' },
  { path: '**', redirectTo: '' },
];
