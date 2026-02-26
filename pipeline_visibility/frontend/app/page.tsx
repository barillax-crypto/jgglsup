"use client";

import { useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Grid2,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchOverview } from "@/lib/dashboardSlice";
import type { AppDispatch, RootState } from "@/lib/store";

function formatCurrency(value: number): string {
  return `${new Intl.NumberFormat("ru-RU").format(value)} ₽`;
}

export default function DashboardPage() {
  const dispatch = useDispatch<AppDispatch>();
  const { overview, loading, error, usingFallback } = useSelector((state: RootState) => state.dashboard);
  const [days, setDays] = useState(30);
  const [orgId, setOrgId] = useState("org-1");

  useEffect(() => {
    dispatch(fetchOverview({ orgId, days }));
  }, [days, dispatch, orgId]);

  const trendData = useMemo(() => overview?.trends ?? [], [overview]);

  const totals = useMemo(() => {
    const rows = overview?.rows ?? [];
    const leads = rows.reduce((acc, row) => acc + row.leads, 0);
    const weightedConversion = leads
      ? rows.reduce((acc, row) => acc + row.conversion_to_deals_pct * row.leads, 0) / leads
      : 0;
    const avgCac = rows.length ? rows.reduce((acc, row) => acc + row.cac, 0) / rows.length : 0;
    return { leads, weightedConversion, avgCac };
  }, [overview]);

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={2}>
          <Box>
            <Typography variant="h4" fontWeight={700}>Pipeline Visibility Dashboard</Typography>
            <Typography color="text.secondary">Аналитика конверсии лидов в выручку для B2B СНГ</Typography>
          </Box>
          <Stack direction="row" spacing={2}>
            <TextField
              size="small"
              label="Org ID"
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
            />
            <Select
              size="small"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
            >
              <MenuItem value={30}>30 дней</MenuItem>
              <MenuItem value={60}>60 дней</MenuItem>
              <MenuItem value={90}>90 дней</MenuItem>
            </Select>
            <Button variant="contained" onClick={() => dispatch(fetchOverview({ orgId, days }))}>
              Обновить
            </Button>
          </Stack>
        </Stack>

        {usingFallback && (
          <Alert severity="info">Backend недоступен, показаны демонстрационные данные.</Alert>
        )}
        {error && <Alert severity="error">{error}</Alert>}
        {overview?.alerts?.map((alert) => (
          <Alert key={alert} severity="warning">{alert}</Alert>
        ))}

        <Grid2 container spacing={2}>
          <Grid2 size={{ xs: 12, md: 4 }}>
            <Card><CardContent><Typography variant="body2" color="text.secondary">Всего лидов</Typography><Typography variant="h5">{totals.leads}</Typography></CardContent></Card>
          </Grid2>
          <Grid2 size={{ xs: 12, md: 4 }}>
            <Card><CardContent><Typography variant="body2" color="text.secondary">Взвешенная конверсия</Typography><Typography variant="h5">{totals.weightedConversion.toFixed(2)}%</Typography></CardContent></Card>
          </Grid2>
          <Grid2 size={{ xs: 12, md: 4 }}>
            <Card><CardContent><Typography variant="body2" color="text.secondary">Средний CAC</Typography><Typography variant="h5">{formatCurrency(Math.round(totals.avgCac))}</Typography></CardContent></Card>
          </Grid2>

          <Grid2 size={{ xs: 12, md: 8 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Источник маркетинга / Лиды / Конверсия / CAC</Typography>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Источник</TableCell>
                      <TableCell>Лиды</TableCell>
                      <TableCell>% в Deals</TableCell>
                      <TableCell>CAC</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(overview?.rows ?? []).map((row) => (
                      <TableRow key={row.source}>
                        <TableCell>{row.source}</TableCell>
                        <TableCell>{row.leads}</TableCell>
                        <TableCell>{row.conversion_to_deals_pct.toFixed(2)}%</TableCell>
                        <TableCell>{formatCurrency(row.cac)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </Grid2>

          <Grid2 size={{ xs: 12, md: 4 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Сравнение с target</Typography>
                <Stack spacing={1}>
                  {(overview?.targets ?? []).map((target) => (
                    <Box key={target.metric}>
                      <Typography fontWeight={600}>{target.metric}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Actual: {target.actual} | Target: {target.target}
                      </Typography>
                      <Chip
                        size="small"
                        color={target.gap_pct <= 0 ? "success" : "error"}
                        label={`Gap ${target.gap_pct}%`}
                      />
                    </Box>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid2>

          <Grid2 size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Тренды по воронке (Leads/Deals/Revenue)</Typography>
                <Box height={320}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="leads" stroke="#1976d2" />
                      <Line type="monotone" dataKey="deals" stroke="#2e7d32" />
                      <Line type="monotone" dataKey="revenue" stroke="#ed6c02" />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              </CardContent>
            </Card>
          </Grid2>

          <Grid2 size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>Top 3 risks/opportunities</Typography>
                <Stack spacing={1}>
                  {(overview?.top_risks_opportunities ?? []).map((item) => (
                    <Box key={item.title}>
                      <Typography fontWeight={600}>{item.title}</Typography>
                      <Typography variant="body2">Impact: {item.impact}</Typography>
                      <Typography variant="body2" color="text.secondary">Recommendation: {item.recommendation}</Typography>
                    </Box>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid2>
        </Grid2>

        {loading && <Typography color="text.secondary">Загрузка...</Typography>}
      </Stack>
    </Container>
  );
}
