FROM node:20-alpine

WORKDIR /workspace

COPY package.json /workspace/package.json
COPY tsconfig.base.json /workspace/tsconfig.base.json
COPY eslint.config.mjs /workspace/eslint.config.mjs
COPY .prettierrc.json /workspace/.prettierrc.json
COPY apps/web/package.json /workspace/apps/web/package.json
COPY apps/mobile/package.json /workspace/apps/mobile/package.json
COPY packages/contracts/package.json /workspace/packages/contracts/package.json
COPY packages/config/package.json /workspace/packages/config/package.json

RUN npm install

COPY . /workspace

CMD ["npm", "run", "dev", "--workspace", "@rtls/web", "--", "--host", "0.0.0.0", "--port", "5173"]
