const routes = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      { path: '', component: () => import('@/pages/IndexPage.vue') },
      { path: '/analytics', component: () => import('@/pages/AnalyticsPage.vue') },
      { path: '/parameters', component: () => import('@/pages/ParametersPage.vue') },
      { path: '/documents', component: () => import('@/pages/DocumentsPage.vue') }
    ]
  },

  {
    path: '/:catchAll(.*)*',
    component: () => import('@/pages/ErrorNotFound.vue')
  }
]

export default routes
