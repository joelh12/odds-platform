FROM node:22-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json tsconfig.base.json ./
COPY packages/shared/package.json packages/shared/package.json
COPY apps/web/package.json apps/web/package.json

RUN npm ci

COPY packages/shared packages/shared
COPY apps/web apps/web

RUN npm run build -w @portfolio/shared \
  && npm run build -w @portfolio/web

FROM node:22-alpine
ENV NODE_ENV=production
WORKDIR /app

COPY --from=builder /app/package.json /app/package-lock.json /app/
COPY --from=builder /app/node_modules /app/node_modules
COPY --from=builder /app/packages/shared /app/packages/shared
COPY --from=builder /app/apps/web /app/apps/web

EXPOSE 3000
CMD ["npm", "run", "start", "-w", "@portfolio/web"]
