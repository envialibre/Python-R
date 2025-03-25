import * as dotenv from 'dotenv';
dotenv.config();

import { APIGatewayProxyHandler } from 'aws-lambda';
import mysql from 'mysql2/promise';

const connectionConfig = {
  host: process.env.RDS_HOST,
  user: process.env.RDS_USER,
  password: process.env.RDS_PASSWORD,
  database: process.env.RDS_DATABASE,
};

console.log("RDS_HOST:", process.env.RDS_HOST);
console.log("RDS_USER:", process.env.RDS_USER);
console.log("RDS_PASSWORD:", process.env.RDS_PASSWORD);
console.log("RDS_DATABASE:", process.env.RDS_DATABASE);

export const getClients: APIGatewayProxyHandler = async (event, context) => {
  const connection = await mysql.createConnection(connectionConfig);
  const [rows] = await connection.execute('SELECT id, name FROM clients');
  await connection.end();
  return {
    statusCode: 200,
    body: JSON.stringify(rows),
  };
};

export const getRequests: APIGatewayProxyHandler = async (event, context) => {
  const { client_id } = event.pathParameters || {};
  if (!client_id) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: 'client_id is required' }),
    };
  }

  const connection = await mysql.createConnection(connectionConfig);
  const [rows]: any = await connection.execute('SELECT api_calls FROM requests WHERE client_id = ?', [client_id]);
  await connection.end();
  return {
    statusCode: 200,
    body: JSON.stringify(rows[0] || {}),
  };
};

export const incrementRequests: APIGatewayProxyHandler = async (event, context) => {
  const { client_id } = event.pathParameters || {};
  if (!client_id) {
    return {
      statusCode: 400,
      body: JSON.stringify({ error: 'client_id is required' }),
    };
  }

  const connection = await mysql.createConnection(connectionConfig);
  await connection.execute('UPDATE requests SET api_calls = api_calls + 1 WHERE client_id = ?', [client_id]);
  await connection.end();
  return {
    statusCode: 200,
    body: JSON.stringify({ message: 'Incremented' }),
  };
};
